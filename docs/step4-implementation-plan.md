# Step 4：前端 + MCP — 实施计划

> 决策版本：接续 Step 3 已完成的后端；本阶段完成全部前端页面 + MCP 工具扩展  
> 生成日期：2026-04-22  
> **主文档**：[PLAN.md](../PLAN.md) — 本文档是其 Step 4 节的执行细化，所有决策以 PLAN.md 为准。

---

## 对照 PLAN.md 需求（零遗漏检查）

| PLAN.md 要求 | 本计划覆盖位置 |
|-------------|--------------|
| 马卡龙主题 CSS 变量 + shadcn/ui 组件库 | Phase 0 · `styles/macaron-theme.css` + `components/macaron/` |
| 面试看板（Kanban） | Phase 2 · `interviews/` 页面 + `KanbanBoard.tsx` |
| OKR 树 | Phase 3 · `okr/` 页面 + `OKRTree.tsx` |
| Agent 对话界面 + WebSocket 推流 | Phase 5 · `agent/` 页面 + `ChatWindow.tsx` |
| 笔记日历页（月视图） | Phase 4 · `notes/page.tsx` + `DailyCalendar.tsx` |
| Milkdown 编辑器 | Phase 4 · `notes/[date]/page.tsx` + `MilkdownEditor.tsx` |
| 反向链接面板 | Phase 4 · `BacklinksPanel.tsx` |
| MCP 工具：`list_notes` / `search_notes_semantic` / `create_daily_note` / `get_note_by_date` | Phase 7 · 新增 3 个 Tool + 修改 `mcp_server.py` |
| MCP 工具：`list_interviews` / `analyze_okr` / `generate_review` | Phase 7 · `list_interviews` 新增；后两者已在 TOOL_REGISTRY，仅确认暴露 |
| i18n（zh-CN / en-US）切换 | Phase 8 · `lib/i18n/` + `next-intl` |

---

## 总览

Step 3 已完成所有后端 + MCP Server 基础；Step 4 目标是：

1. **搭建 Next.js 14 前端**：脚手架 → 认证 → 四大业务页面 → 设置页  
2. **扩展 MCP 工具注册表**：新增 3 个 Tool 文件，保证外部客户端（Claude Desktop / Cursor / Obsidian）可直接调用笔记与面试工具  
3. **i18n**：中英双语，运行时切换

| 类别 | 新建 | 修改 | 小计 |
|------|------|------|------|
| 前端脚手架 & 主题 | 8 | 0 | 8 |
| 基础布局 & 认证页 | 7 | 0 | 7 |
| 面试模块 | 6 | 0 | 6 |
| OKR 模块 | 5 | 0 | 5 |
| 笔记模块 | 6 | 0 | 6 |
| Agent 对话界面 | 4 | 0 | 4 |
| 设置页 | 3 | 0 | 3 |
| 公共库（API client / Store / Hooks） | 8 | 0 | 8 |
| 后端 MCP Tool 新增 | 3 | 1 | 4 |
| i18n | 3 | 0 | 3 |
| **合计** | **53** | **1** | **54** |

---

## 文件树（Step 4 新增 / 修改）

```
frontend/
├── package.json                              ← NEW
├── next.config.ts                            ← NEW
├── tailwind.config.ts                        ← NEW
├── tsconfig.json                             ← NEW
├── .env.local.example                        ← NEW
├── styles/
│   └── macaron-theme.css                     ← NEW: CSS 变量（马卡龙色板）
├── app/
│   ├── layout.tsx                            ← NEW: 根布局 + i18n Provider
│   ├── globals.css                           ← NEW
│   ├── (auth)/
│   │   ├── login/page.tsx                    ← NEW: 邮箱 + 密码登录
│   │   ├── register/page.tsx                 ← NEW: 注册页
│   │   └── google-callback/page.tsx          ← NEW: OAuth 回调页
│   └── (dashboard)/
│       ├── layout.tsx                        ← NEW: Sidebar + Topbar 布局
│       ├── page.tsx                          ← NEW: 仪表盘首页（统计卡片）
│       ├── interviews/
│       │   ├── page.tsx                      ← NEW: 看板视图（Kanban）
│       │   ├── [id]/page.tsx                 ← NEW: 面试详情 + 复盘报告
│       │   └── components/
│       │       ├── KanbanBoard.tsx           ← NEW: DnD 看板
│       │       ├── InterviewCard.tsx         ← NEW
│       │       └── ReviewPanel.tsx           ← NEW: 复盘报告展示
│       ├── okr/
│       │   ├── page.tsx                      ← NEW: OKR 列表 + 进度环
│       │   └── components/
│       │       ├── OKRTree.tsx               ← NEW: 树形 O→KR 折叠展示
│       │       ├── KRProgressBar.tsx         ← NEW
│       │       └── DailyTaskList.tsx         ← NEW
│       ├── notes/
│       │   ├── page.tsx                      ← NEW: 月历视图 + 侧边笔记列表
│       │   ├── [date]/page.tsx               ← NEW: 单日笔记详情 + 编辑
│       │   └── components/
│       │       ├── MilkdownEditor.tsx        ← NEW: 所见即所得 Markdown
│       │       ├── DailyCalendar.tsx         ← NEW: 月历（有笔记的日期高亮）
│       │       └── BacklinksPanel.tsx        ← NEW: 反向链接 + 标签云
│       ├── agent/
│       │   ├── page.tsx                      ← NEW: Agent 对话主页
│       │   └── components/
│       │       ├── ChatWindow.tsx            ← NEW: 消息气泡 + 流式输出
│       │       ├── MessageBubble.tsx         ← NEW
│       │       └── TaskProgressBar.tsx       ← NEW: WebSocket 进度条
│       └── settings/
│           ├── page.tsx                      ← NEW: 用户设置主页
│           └── components/
│               ├── ApiKeyForm.tsx            ← NEW: LLM API Key 管理
│               └── LanguageToggle.tsx        ← NEW: 语言切换
├── components/
│   ├── ui/                                   ← NEW: shadcn/ui 自动生成组件目录
│   └── macaron/
│       ├── MacaronCard.tsx                   ← NEW: 马卡龙圆角卡片
│       ├── MacaronBadge.tsx                  ← NEW: 状态徽章
│       └── Sidebar.tsx                       ← NEW: 全局侧边导航
└── lib/
    ├── api.ts                                ← NEW: axios 实例 + 拦截器（JWT 注入）
    ├── api/
    │   ├── interviews.ts                     ← NEW: 面试 CRUD hooks
    │   ├── okr.ts                            ← NEW: OKR CRUD hooks
    │   ├── notes.ts                          ← NEW: 笔记 CRUD hooks
    │   └── agent.ts                          ← NEW: Agent chat + WS hooks
    ├── store/
    │   ├── authStore.ts                      ← NEW: Zustand 用户状态
    │   └── settingsStore.ts                  ← NEW: 语言 / 主题偏好
    └── i18n/
        ├── zh-CN.ts                          ← NEW: 中文词条
        └── en-US.ts                          ← NEW: 英文词条

backend/app/
└── agents/
    ├── tools/
    │   ├── list_notes.py                     ← NEW: 列出用户笔记（支持分页 + 标签过滤）
    │   ├── get_note_by_date.py               ← NEW: 按日期精确获取笔记内容
    │   └── list_interviews.py                ← NEW: 列出面试记录（支持状态过滤）
    └── mcp_server.py                         ← MODIFY: 确认新 3 个 Tool 自动注册到 TOOL_REGISTRY
```

---

## 实现阶段

| 阶段 | 内容 | 文件数 | 估算工作量 |
|------|------|--------|-----------|
| 0 · 脚手架 & 主题 | Next.js 14 初始化、Tailwind、shadcn/ui、马卡龙 CSS 变量 | 8 | 低 |
| 1 · 布局 & 认证 | Sidebar、Topbar、登录/注册/Google OAuth 回调 | 7 | 中 |
| 2 · 面试看板 | Kanban（DnD）、面试详情、复盘报告展示 | 6 | 中高 |
| 3 · OKR 树 | O→KR 折叠树、进度条、日常任务列表 | 5 | 中 |
| 4 · 笔记模块 | 月历视图、Milkdown 编辑器、反向链接面板 | 6 | 高 |
| 5 · Agent 对话 | WebSocket 实时流、消息气泡、进度条 | 4 | 中高 |
| 6 · 设置页 | API Key 表单、语言切换 | 3 | 低 |
| 7 · MCP 工具扩展 | 3 个新 Tool + mcp_server.py 确认注册 | 4 | 中 |
| 8 · i18n | next-intl 配置 + zh-CN / en-US 词条 | 3 | 低 |

---

## 关键技术决策

### Phase 0：脚手架 & 马卡龙主题

#### `styles/macaron-theme.css` — CSS 变量定义

```css
:root {
  /* 马卡龙色板 */
  --color-macaron-pink:   #F7C5C5;
  --color-macaron-mint:   #C5EAD5;
  --color-macaron-lemon:  #F9F0C5;
  --color-macaron-lilac:  #D5C5EA;
  --color-macaron-sky:    #C5DCF7;
  --color-macaron-peach:  #F7DEC5;

  /* 语义 Token */
  --color-primary:        var(--color-macaron-pink);
  --color-secondary:      var(--color-macaron-mint);
  --color-accent:         var(--color-macaron-lilac);
  --color-surface:        #FFFAF8;
  --color-text:           #3D2B2B;
  --color-text-muted:     #9B8080;
  --color-border:         #EDD8D8;

  /* 圆角 */
  --radius-sm: 8px;
  --radius-md: 16px;
  --radius-lg: 24px;
}
```

#### `tailwind.config.ts` 扩展

```ts
extend: {
  colors: {
    macaron: {
      pink: 'var(--color-macaron-pink)',
      mint: 'var(--color-macaron-mint)',
      lemon: 'var(--color-macaron-lemon)',
      lilac: 'var(--color-macaron-lilac)',
      sky: 'var(--color-macaron-sky)',
      peach: 'var(--color-macaron-peach)',
    }
  },
  borderRadius: {
    lg: 'var(--radius-lg)',
    md: 'var(--radius-md)',
  }
}
```

#### `package.json` 核心依赖

```json
{
  "dependencies": {
    "next": "14.2.x",
    "@milkdown/core": "^7.x",
    "@milkdown/react": "^7.x",
    "@milkdown/preset-commonmark": "^7.x",
    "@milkdown/plugin-history": "^7.x",
    "@dnd-kit/core": "^6.x",
    "@dnd-kit/sortable": "^8.x",
    "@tanstack/react-query": "^5.x",
    "zustand": "^4.x",
    "next-intl": "^3.x",
    "framer-motion": "^11.x",
    "axios": "^1.x",
    "date-fns": "^3.x",
    "recharts": "^2.x",
    "tailwindcss": "^3.x",
    "shadcn-ui": "latest"
  }
}
```

---

### Phase 1：基础布局 & 认证

#### `app/(dashboard)/layout.tsx` — 侧边栏布局

```tsx
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-[--color-surface]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
```

#### `components/macaron/Sidebar.tsx` — 导航项

| 路由 | 图标 | 标签 |
|------|------|------|
| `/interviews` | `BriefcaseIcon` | 面试看板 / Interviews |
| `/okr` | `TargetIcon` | OKR 规划 / OKR |
| `/notes` | `BookOpenIcon` | 学习笔记 / Notes |
| `/agent` | `SparklesIcon` | AI 助手 / Assistant |
| `/settings` | `SettingsIcon` | 设置 / Settings |

#### 认证流程

```
登录页 → POST /api/v1/auth/login → 存 access_token + refresh_token 到 httpOnly Cookie
注册页 → POST /api/v1/auth/register → 自动登录
Google OAuth → GET /api/v1/auth/google → 重定向 Google → /google-callback?code=xxx → 换 JWT
```

`lib/api.ts` axios 拦截器：
- **Request**：从 Cookie 取 `access_token`，注入 `Authorization: Bearer`
- **Response 401**：自动调用 `/auth/refresh`，重试原请求；再次 401 → 跳转登录页

---

### Phase 2：面试看板

#### `KanbanBoard.tsx` — DnD 看板

```
看板列（status 字段）：
  投递 → 笔试 → 一面 → 二面 → HR面 → Offer → 拒绝
```

- 使用 `@dnd-kit/core` + `@dnd-kit/sortable` 拖拽卡片跨列
- 拖拽结束后调用 `PATCH /api/v1/interviews/{id}` 更新 `status`
- TanStack Query `useMutation` + 乐观更新（拖拽即时响应，失败时回滚）

#### `ReviewPanel.tsx` — 复盘报告

- 调用 `POST /api/v1/agent/chat`（message："生成 {interview_id} 的复盘"）
- 订阅 WebSocket `/ws/tasks/{task_id}` 接收流式进度
- Markdown 渲染：`react-markdown` + `rehype-highlight`（代码高亮）

---

### Phase 3：OKR 树

#### `OKRTree.tsx` — 折叠树

```
Objective（卡片，进度环 recharts RadialBarChart）
  └── KR 1（进度条 + 百分比）
        └── DailyTask 列表（checkbox）
  └── KR 2
  └── ...
```

- 数据：`GET /api/v1/okr` 返回 `{ objectives: [{ key_results: [...] }] }`
- 折叠状态：`useState<Set<string>>` 管理已展开 Objective ID
- KR 打卡：`PATCH /api/v1/okr/kr/{id}` 更新 `current_value`

---

### Phase 4：笔记模块

#### `DailyCalendar.tsx` — 月历视图

```
依赖：date-fns（月份计算）

渲染逻辑：
  GET /api/v1/notes?month=2026-04
  → 返回 [{ date, title, word_count, tags }]
  → 有笔记的日期渲染马卡龙色圆点
  → 点击日期 → 路由 /notes/2026-04-22
```

#### `MilkdownEditor.tsx` — Milkdown 集成

```tsx
import { Editor, rootCtx, defaultValueCtx } from '@milkdown/core';
import { commonmark } from '@milkdown/preset-commonmark';
import { history } from '@milkdown/plugin-history';
import { ReactEditor, useEditor } from '@milkdown/react';

export function MilkdownEditor({ content, onChange }: Props) {
  const { get } = useEditor((root) =>
    Editor.make()
      .config((ctx) => {
        ctx.set(rootCtx, root);
        ctx.set(defaultValueCtx, content);
      })
      .use(commonmark)
      .use(history)
  );

  // 防抖 500ms 保存
  const debouncedSave = useDebouncedCallback((md: string) => onChange(md), 500);

  return <ReactEditor editor={get()} />;
}
```

保存流程：`onChange` → `PATCH /api/v1/notes/{date}` → 后端写文件 + 触发 embedding 任务

#### `BacklinksPanel.tsx` — 反向链接

```
GET /api/v1/notes/{date}/backlinks
  → 返回 [{ source_date, source_title, excerpt }]

GET /api/v1/notes/{date}/tags
  → 返回 [{ tag, count }]（标签云）
```

---

### Phase 5：Agent 对话界面

#### `ChatWindow.tsx` — WebSocket 实时流

```tsx
function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const sendMessage = async (text: string) => {
    // 1. 投递消息
    const { task_id } = await agentApi.chat(text);

    // 2. 连接 WebSocket
    wsRef.current = new WebSocket(`ws://localhost:8000/ws/tasks/${task_id}`);
    wsRef.current.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.stage === 'delta') {
        setMessages(prev => appendDelta(prev, data.delta));
      }
      if (data.stage === 'done') {
        wsRef.current?.close();
      }
    };
  };

  return (
    <div className="flex flex-col h-full">
      <MessageList messages={messages} />
      <MessageInput onSend={sendMessage} />
    </div>
  );
}
```

进度阶段显示：

| stage | 显示文案 |
|-------|---------|
| `supervisor` | 🧠 意图识别中… |
| `interview_agent` | 📋 面试分析中… |
| `notes_agent` | 📚 笔记检索中… |
| `okr_agent` | 🎯 OKR 分析中… |
| `memory_agent` | 💾 记忆检索中… |
| `done` | ✅ 完成 |

---

### Phase 6：设置页

#### `ApiKeyForm.tsx` — LLM Key 管理

```
字段：
  - 默认 LLM Provider（下拉：Claude / OpenAI / DeepSeek / Qwen / Gemini）
  - 默认 API Key（password input）
  - 每个 Agent 独立 Key（Interview / Notes / OKR / Memory Agent 各一个折叠面板）

PATCH /api/v1/users/me/settings → 更新 agent_llm_assignments 表
```

---

### Phase 7：MCP 工具扩展

#### 新增 `backend/app/agents/tools/list_notes.py`

```python
class ListNotesTool(BaseTool):
    tool_schema = {
        "name": "list_notes",
        "description": "列出用户的每日笔记列表，支持月份过滤和标签过滤",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "month":   {"type": "string", "description": "格式 YYYY-MM，不传则返回最近 30 天"},
                "tag":     {"type": "string", "description": "标签过滤，可选"},
                "limit":   {"type": "integer", "default": 20},
            },
            "required": ["user_id"],
        },
    }

    async def execute(self, user_id: str, month: str = "", tag: str = "", limit: int = 20, **_) -> dict:
        # SELECT id, date, title, word_count, tags FROM notes WHERE user_id=:uid ...
        ...
```

#### 新增 `backend/app/agents/tools/get_note_by_date.py`

```python
class GetNoteByDateTool(BaseTool):
    tool_schema = {
        "name": "get_note_by_date",
        "description": "根据日期精确获取用户笔记的完整 Markdown 内容及 frontmatter",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "date":    {"type": "string", "description": "格式 YYYY-MM-DD"},
            },
            "required": ["user_id", "date"],
        },
    }

    async def execute(self, user_id: str, date: str, **_) -> dict:
        # 读文件 vault/{user_id}/daily/{date}.md → 返回 {content, frontmatter, backlinks}
        ...
```

#### 新增 `backend/app/agents/tools/list_interviews.py`

```python
class ListInterviewsTool(BaseTool):
    tool_schema = {
        "name": "list_interviews",
        "description": "列出用户的面试记录，支持状态过滤",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "status":  {"type": "string", "description": "可选：投递/一面/Offer/拒绝 等"},
                "limit":   {"type": "integer", "default": 20},
            },
            "required": ["user_id"],
        },
    }

    async def execute(self, user_id: str, status: str = "", limit: int = 20, **_) -> dict:
        # SELECT interviews + companies JOIN WHERE user_id=:uid ...
        ...
```

#### 修改 `backend/app/agents/mcp_server.py`

只需确认 `list_tools()` 遍历 `TOOL_REGISTRY` 时自动包含上述 3 个新 Tool。无需额外改动，因为 `@register_tool` 装饰器会在导入时自动注册。

```python
# mcp_server.py 顶部确保导入新 Tool 模块（触发 @register_tool 注册）
from app.agents.tools import list_notes        # noqa: F401
from app.agents.tools import get_note_by_date  # noqa: F401
from app.agents.tools import list_interviews   # noqa: F401
```

**Step 4 完成后，MCP 对外暴露全部工具**：

| MCP Tool 名称 | 对应 Tool 类 | 状态 |
|--------------|------------|------|
| `list_notes` | `ListNotesTool` | Step 4 新增 |
| `get_note_by_date` | `GetNoteByDateTool` | Step 4 新增 |
| `list_interviews` | `ListInterviewsTool` | Step 4 新增 |
| `search_notes_semantic` | `SearchNotesTool`（已有） | Step 3 已完成 |
| `create_daily_note` | `DailyNoteAssistantTool`（已有） | Step 3 已完成 |
| `analyze_okr` | `AnalyzeOKRTool`（已有） | Step 3 已完成 |
| `generate_review` | `GenerateReviewTool`（已有） | Step 3 已完成 |
| `search_questions` | `SearchQuestionsTool`（已有） | Step 3 已完成 |
| `analyze_status` | `AnalyzeStatusTool`（已有） | Step 3 已完成 |
| `suggest_tasks` | `SuggestTasksTool`（已有） | Step 3 已完成 |
| `generate_report` | `GenerateReportTool`（已有） | Step 3 已完成 |
| `create_summary` | `CreateSummaryTool`（已有） | Step 3 已完成 |

---

### Phase 8：i18n

#### 使用 `next-intl`

```
lib/i18n/zh-CN.ts — 中文词条（默认）
lib/i18n/en-US.ts — 英文词条

app/layout.tsx → NextIntlClientProvider locale={locale}

LanguageToggle.tsx → 切换 Cookie locale → next-intl 中间件响应
```

词条示例（`zh-CN.ts`）：

```ts
export default {
  nav: {
    interviews: '面试看板',
    okr: 'OKR 规划',
    notes: '学习笔记',
    agent: 'AI 助手',
    settings: '设置',
  },
  interviews: {
    status: {
      applied: '已投递',
      technical: '技术面',
      offer: 'Offer',
      rejected: '拒绝',
    },
  },
  notes: {
    editor_placeholder: '开始记录今天的学习...',
    calendar_empty: '当天暂无笔记',
  },
  agent: {
    thinking: '思考中...',
    done: '完成',
  },
};
```

---

## 新增前端环境变量（`.env.local.example`）

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
```

---

## 非功能性实现清单

| 需求 | 实现方案 | 位置 |
|------|---------|------|
| Token 无感刷新 | axios response 拦截器：401 → `/auth/refresh` → 重试 | `lib/api.ts` |
| 编辑器防抖保存 | `useDebouncedCallback(500ms)` → PATCH | `MilkdownEditor.tsx` |
| WebSocket 断线重连 | exponential backoff，最多 5 次 | `lib/api/agent.ts` |
| 看板乐观更新 | TanStack Query `useMutation` + `onMutate` 乐观写 + `onError` 回滚 | `KanbanBoard.tsx` |
| 路由守卫 | Next.js middleware：无 token → 重定向 `/login` | `middleware.ts` |
| 响应式布局 | Tailwind `md:` / `lg:` 断点；移动端 Sidebar 折叠 | `Sidebar.tsx` |
| SEO / 元数据 | Next.js 14 `generateMetadata()` | 各页面 |

---

## 验证计划

```bash
# 1. 启动后端（Step 3 已完成）
cd backend && uvicorn app.main:app --reload --port 8000

# 2. 安装前端依赖
cd frontend && npm install

# 3. 初始化 shadcn/ui
npx shadcn-ui@latest init

# 4. 启动前端开发服务器
npm run dev
# → http://localhost:3000

# 5. 认证流程测试
# 注册 → 登录 → 查看 Sidebar 是否正常渲染

# 6. 面试看板测试
# 创建面试记录 → 拖拽状态列 → 检查后端 status 更新

# 7. 笔记模块测试
# 打开月历 → 点击今天 → Milkdown 编辑内容 → 等待 500ms 自动保存
# → 检查 vault/{user_id}/daily/2026-04-22.md 文件是否更新

# 8. Agent 对话测试
# 发送「帮我分析最近的笔记」→ 检查 WebSocket 流式输出各阶段标签

# 9. MCP 工具 smoke test（扩展后）
echo '{"method":"tools/list"}' | python -m app.agents.mcp_server
# → 应包含 list_notes / get_note_by_date / list_interviews

echo '{"method":"tools/call","params":{"name":"list_notes","arguments":{"user_id":"test-uid"}}}' \
  | python -m app.agents.mcp_server

# 10. i18n 切换测试
# 设置页点击 EN → 检查所有标签切换为英文
```

---

## 相关文档

- [step3-implementation-plan.md](step3-implementation-plan.md) — Step 3 后端实现
- [step2-implementation-plan.md](step2-implementation-plan.md) — Step 2 骨架说明
- [architecture.md](architecture.md) — 系统架构 + 请求时序图
- [notes-vault-spec.md](notes-vault-spec.md) — Markdown Vault 规范
- [PLAN.md](../PLAN.md) — 全局开发计划
