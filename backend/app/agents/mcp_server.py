"""
MCP Server 配置（基于 mcp Python SDK）。
暴露 Skills 给 Obsidian / Claude Desktop。
"""
# import mcp.server.stdio
# from mcp.server import Server
# from mcp.types import Tool, TextContent, CallToolResult

# server = Server("lumipath-mcp")

# @server.list_tools()
# async def list_tools() -> list[Tool]:
#     # TODO: list skills from SKILL_REGISTRY
#     return []

# @server.call_tool()
# async def call_tool(name: str, arguments: dict) -> list[TextContent]:
#     # TODO: dispatch to SKILL_REGISTRY
#     return [TextContent(type="text", text="mcp server stub")]

# async def main():
#     # async with mcp.server.stdio.stdio_server() as (read, write):
#     #     await server.run(read, write, None)
#     pass

# if __name__ == "__main__":
#     import asyncio
#     # asyncio.run(main())
