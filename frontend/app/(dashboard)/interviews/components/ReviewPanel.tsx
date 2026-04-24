"use client";
import { useState, useRef, useEffect } from "react";
import { toast } from "sonner";
import { agentApi } from "@/lib/api/agent";
import { WS_BASE } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import { SparklesIcon } from "lucide-react";

interface ReviewPanelProps {
  interviewId: string;
  existingReview?: string;
}

export function ReviewPanel({ interviewId, existingReview }: ReviewPanelProps) {
  const [review, setReview] = useState(existingReview ?? "");
  const [generating, setGenerating] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => () => wsRef.current?.close(), []);

  const generate = async () => {
    setGenerating(true);
    setReview("");
    try {
      const { task_id } = await agentApi.chat(
        `请帮我生成面试复盘报告，面试 ID: ${interviewId}`
      );

      wsRef.current = new WebSocket(`${WS_BASE}/ws/tasks/${task_id}`);
      wsRef.current.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.stage === "delta" && data.delta) {
          setReview((prev) => prev + data.delta);
        }
        if (data.stage === "done" || data.stage === "error") {
          setGenerating(false);
          wsRef.current?.close();
          if (data.stage === "error") toast.error("复盘生成失败");
        }
      };
      wsRef.current.onerror = () => {
        setGenerating(false);
        toast.error("WebSocket 连接失败");
      };
    } catch {
      setGenerating(false);
      toast.error("请求失败，请重试");
    }
  };

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-text-main text-sm">AI 复盘报告</h3>
        <button
          onClick={generate}
          disabled={generating}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-macaron-lilac text-text-main text-xs font-medium hover:bg-[--color-accent-dark] transition-colors disabled:opacity-60"
        >
          <SparklesIcon className="w-3.5 h-3.5" strokeWidth={1.5} />
          {generating ? "生成中…" : "生成复盘"}
        </button>
      </div>

      {review ? (
        <div className="macaron-card p-4 prose prose-sm max-w-none text-text-main">
          <ReactMarkdown>{review}</ReactMarkdown>
        </div>
      ) : (
        <div className="macaron-card p-6 text-center text-text-muted text-sm">
          {generating
            ? "正在生成复盘报告，请稍候…"
            : "点击「生成复盘」让 AI 分析这场面试"}
        </div>
      )}
    </div>
  );
}
