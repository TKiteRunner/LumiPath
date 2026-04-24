import { cn } from "@/lib/utils";

const STAGES = [
  "supervisor",
  "interview_agent",
  "notes_agent",
  "okr_agent",
  "memory_agent",
  "done",
];

const STAGE_LABELS: Record<string, string> = {
  supervisor: "意图识别",
  interview_agent: "面试分析",
  notes_agent: "笔记检索",
  okr_agent: "OKR 分析",
  memory_agent: "记忆检索",
  done: "完成",
};

export function TaskProgressBar({ currentStage }: { currentStage: string }) {
  const idx = STAGES.indexOf(currentStage);

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {STAGES.map((stage, i) => (
        <div key={stage} className="flex items-center gap-1">
          <span
            className={cn(
              "text-xs px-2 py-0.5 rounded-full transition-all",
              i < idx
                ? "bg-macaron-mint text-text-main"
                : i === idx
                ? "bg-macaron-lilac text-text-main font-semibold animate-pulse"
                : "bg-border text-text-muted"
            )}
          >
            {STAGE_LABELS[stage]}
          </span>
          {i < STAGES.length - 1 && (
            <span className="text-border text-xs">›</span>
          )}
        </div>
      ))}
    </div>
  );
}
