import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  stage?: string;
}

const STAGE_LABELS: Record<string, string> = {
  supervisor: "🧠 意图识别中…",
  interview_agent: "📋 面试分析中…",
  notes_agent: "📚 笔记检索中…",
  okr_agent: "🎯 OKR 分析中…",
  memory_agent: "💾 记忆检索中…",
  done: "✅ 完成",
  error: "❌ 出错了",
};

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex gap-3 animate-slide-up",
        isUser && "flex-row-reverse"
      )}
    >
      {/* 头像 */}
      <div
        className={cn(
          "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5",
          isUser
            ? "bg-macaron-pink text-text-main"
            : "bg-macaron-lilac text-text-main"
        )}
      >
        {isUser ? "你" : "AI"}
      </div>

      {/* 气泡 */}
      <div className={cn("max-w-[75%]", isUser && "items-end flex flex-col")}>
        {message.stage && message.stage !== "delta" && message.stage !== "done" && (
          <span className="text-xs text-text-muted mb-1 block">
            {STAGE_LABELS[message.stage] ?? message.stage}
          </span>
        )}
        <div
          className={cn(
            "px-4 py-2.5 rounded-2xl text-sm leading-relaxed",
            isUser
              ? "bg-macaron-pink text-text-main rounded-tr-sm"
              : "bg-white border border-border text-text-main rounded-tl-sm macaron-card"
          )}
        >
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none text-text-main">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
