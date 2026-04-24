"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { agentApi } from "@/lib/api/agent";
import { WS_BASE } from "@/lib/api";
import { MessageBubble, type Message } from "./MessageBubble";
import { TaskProgressBar } from "./TaskProgressBar";
import { SendIcon } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const MAX_RETRIES = 5;

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [currentStage, setCurrentStage] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();

  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const retriesRef = useRef(0);

  const scrollToBottom = () => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWs = useCallback(
    (taskId: string) => {
      const connect = (delay = 0) => {
        setTimeout(() => {
          const ws = new WebSocket(`${WS_BASE}/ws/tasks/${taskId}`);
          wsRef.current = ws;

          ws.onmessage = (e) => {
            const data = JSON.parse(e.data);

            if (data.stage === "delta" && data.delta) {
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last && last.role === "assistant") {
                  return [
                    ...prev.slice(0, -1),
                    { ...last, content: last.content + data.delta },
                  ];
                }
                return [
                  ...prev,
                  {
                    id: crypto.randomUUID(),
                    role: "assistant",
                    content: data.delta,
                  },
                ];
              });
            } else if (data.stage && data.stage !== "delta") {
              setCurrentStage(data.stage);
              if (data.stage === "done" || data.stage === "error") {
                setSending(false);
                setCurrentStage("");
                ws.close();
                if (data.stage === "error")
                  toast.error("AI 处理出现错误，请重试");
              }
            }
          };

          ws.onerror = () => {
            if (retriesRef.current < MAX_RETRIES) {
              retriesRef.current++;
              connect(Math.min(1000 * 2 ** retriesRef.current, 10000));
            } else {
              setSending(false);
              toast.error("连接失败，请刷新页面后重试");
            }
          };

          ws.onclose = () => {
            retriesRef.current = 0;
          };
        }, delay);
      };

      connect();
    },
    []
  );

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) return;

    setInput("");
    setSending(true);
    setCurrentStage("supervisor");

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const { task_id, session_id } = await agentApi.chat(text, sessionId);
      setSessionId(session_id);
      retriesRef.current = 0;
      connectWs(task_id);
    } catch {
      setSending(false);
      setCurrentStage("");
      toast.error("发送失败，请重试");
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* 消息列表 */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-6 py-4 space-y-4"
      >
        {messages.length === 0 && (
          <div className="text-center py-16">
            <p className="text-text-muted text-sm">
              和 AI 助手对话，让它帮你分析面试、规划 OKR、整理笔记
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {[
                "帮我复盘最近一次面试",
                "分析我的 OKR 完成情况",
                "总结本周学习笔记",
              ].map((hint) => (
                <button
                  key={hint}
                  onClick={() => setInput(hint)}
                  className="px-3 py-1.5 rounded-full text-xs border border-border text-text-muted hover:bg-macaron-pink/10 hover:text-text-main transition-colors"
                >
                  {hint}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
      </div>

      {/* 进度条 */}
      {sending && currentStage && (
        <div className="px-6 py-2 border-t border-border">
          <TaskProgressBar currentStage={currentStage} />
        </div>
      )}

      {/* 输入框 */}
      <div className="px-6 py-4 border-t border-border bg-white">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage();
          }}
          className="flex gap-3 items-end"
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="向 AI 助手提问… (Enter 发送，Shift+Enter 换行)"
            rows={1}
            disabled={sending}
            className="flex-1 resize-none px-4 py-2.5 rounded-xl border border-border text-sm text-text-main placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-macaron-pink/50 disabled:opacity-60 max-h-32 overflow-y-auto"
            style={{ lineHeight: "1.6" }}
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className={cn(
              "w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors",
              input.trim() && !sending
                ? "bg-macaron-pink hover:bg-[--color-primary-dark]"
                : "bg-border cursor-not-allowed"
            )}
          >
            <SendIcon className="w-4 h-4 text-text-main" strokeWidth={1.5} />
          </button>
        </form>
      </div>
    </div>
  );
}
