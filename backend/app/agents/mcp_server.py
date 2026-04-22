"""
MCP Server — stdio + SSE 双模式。
将 TOOL_REGISTRY 中的全部 Tool 暴露给 Claude Desktop / Cursor / Obsidian 插件。

启动方式：
  stdio:  python -m app.agents.mcp_server
  SSE:    uvicorn app.agents.mcp_server:sse_app --port 8765
"""
from __future__ import annotations

import asyncio
import json
import structlog
from typing import Any

logger = structlog.get_logger(__name__)


# ── 工具注册加载 ──────────────────────────────────────────────────────────────
def _load_tool_registry() -> dict:
    from app.agents.tools import TOOL_REGISTRY
    return TOOL_REGISTRY


# ── MCP stdio 模式 ────────────────────────────────────────────────────────────

async def _run_stdio() -> None:
    """通过 stdin/stdout 实现 MCP JSON-RPC 协议（stdio transport）。"""
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

    TOOL_REGISTRY = _load_tool_registry()
    server = Server("lumipath-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        tools = []
        for name, cls in TOOL_REGISTRY.items():
            try:
                instance = cls.__new__(cls)
                instance.user_id = ""
                schema = instance.tool_schema
                tools.append(
                    Tool(
                        name=name,
                        description=schema.get("description", ""),
                        inputSchema=schema.get("parameters", {"type": "object", "properties": {}}),
                    )
                )
            except Exception as exc:
                logger.warning("Failed to load tool schema", tool=name, error=str(exc))
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name not in TOOL_REGISTRY:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
        try:
            # MCP 调用时 user_id 由 arguments 传入（MCP client 负责提供）
            user_id = arguments.pop("user_id", "mcp-anonymous")
            cls = TOOL_REGISTRY[name]
            instance = cls.__new__(cls)
            instance.user_id = user_id
            result = await instance.execute(user_id=user_id, **arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
        except Exception as exc:
            logger.error("MCP tool call failed", tool=name, error=str(exc))
            return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]

    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP stdio server started")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


# ── MCP SSE 模式（FastAPI 挂载）───────────────────────────────────────────────

def create_sse_app():
    """
    创建 FastAPI SSE 应用，可独立运行也可挂载到主 app：
        main_app.mount("/mcp", mcp_server.create_sse_app())
    """
    try:
        from mcp.server.sse import SseServerTransport
        from mcp.server import Server
        from mcp.types import Tool, TextContent
        from fastapi import FastAPI, Request
        from fastapi.responses import StreamingResponse
    except ImportError:
        logger.warning("mcp package not installed; SSE MCP server disabled")
        from fastapi import FastAPI
        app = FastAPI()

        @app.get("/health")
        async def health():
            return {"status": "mcp_disabled", "reason": "mcp package not installed"}

        return app

    TOOL_REGISTRY = _load_tool_registry()
    server = Server("lumipath-mcp-sse")
    transport = SseServerTransport("/mcp/messages")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        tools = []
        for name, cls in TOOL_REGISTRY.items():
            try:
                instance = cls.__new__(cls)
                instance.user_id = ""
                schema = instance.tool_schema
                tools.append(Tool(
                    name=name,
                    description=schema.get("description", ""),
                    inputSchema=schema.get("parameters", {"type": "object", "properties": {}}),
                ))
            except Exception:
                pass
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name not in TOOL_REGISTRY:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
        try:
            user_id = arguments.pop("user_id", "mcp-anonymous")
            cls = TOOL_REGISTRY[name]
            instance = cls.__new__(cls)
            instance.user_id = user_id
            result = await instance.execute(user_id=user_id, **arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
        except Exception as exc:
            return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]

    app = FastAPI(title="LumiPath MCP SSE Server")

    @app.get("/sse")
    async def sse_endpoint(request: Request):
        async with transport.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())

    @app.post("/messages")
    async def message_endpoint(request: Request):
        await transport.handle_post_message(request.scope, request.receive, request._send)

    @app.get("/health")
    async def health():
        return {"status": "ok", "tools": list(TOOL_REGISTRY.keys())}

    return app


# 供 uvicorn 直接挂载的 SSE app 实例
sse_app = create_sse_app()

# ── 入口（stdio 模式）────────────────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(_run_stdio())
