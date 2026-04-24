import { ChatWindow } from "./components/ChatWindow";

export default function AgentPage() {
  return (
    <div className="h-screen flex flex-col">
      <div className="px-6 py-4 border-b border-border bg-white flex-shrink-0">
        <h1 className="text-xl font-bold text-text-main">AI 助手</h1>
        <p className="text-text-muted text-sm mt-0.5">
          多智能体协作 · 面试复盘 / OKR 规划 / 笔记总结
        </p>
      </div>
      <div className="flex-1 overflow-hidden bg-surface">
        <ChatWindow />
      </div>
    </div>
  );
}
