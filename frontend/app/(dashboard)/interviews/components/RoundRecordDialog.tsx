"use client";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { interviewsApi, InterviewStatus } from "@/lib/api/interviews";
import { PlusIcon, TrashIcon, XIcon } from "lucide-react";
import { toast } from "sonner";

const STAGE_LABELS: Record<string, string> = {
  written_test: "笔试",
  first_interview: "一面",
  second_interview: "二面",
  third_interview: "三面",
  fourth_interview: "四面",
  hr_interview: "HR 面",
};

interface QuestionDraft {
  key: number;
  text: string;
  answer: string;
}

interface Props {
  interviewId: string;
  stage: InterviewStatus;
  onClose: () => void;
}

export function RoundRecordDialog({ interviewId, stage, onClose }: Props) {
  const queryClient = useQueryClient();
  const [questions, setQuestions] = useState<QuestionDraft[]>([
    { key: Date.now(), text: "", answer: "" },
  ]);
  const [notes, setNotes] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const addRow = () =>
    setQuestions((prev) => [...prev, { key: Date.now(), text: "", answer: "" }]);

  const removeRow = (key: number) =>
    setQuestions((prev) => prev.filter((q) => q.key !== key));

  const updateRow = (key: number, field: "text" | "answer", value: string) =>
    setQuestions((prev) =>
      prev.map((q) => (q.key === key ? { ...q, [field]: value } : q))
    );

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const filled = questions.filter((q) => q.text.trim());
      await Promise.all(
        filled.map((q) =>
          interviewsApi.addQuestion(interviewId, {
            question_text: q.text.trim(),
            my_answer: q.answer.trim() || undefined,
            category: stage,
          })
        )
      );
      if (notes.trim()) {
        await interviewsApi.update(interviewId, { notes: notes.trim() });
      }
      queryClient.invalidateQueries({ queryKey: ["interview-questions", interviewId] });
      queryClient.invalidateQueries({ queryKey: ["interview", interviewId] });
      toast.success(`${STAGE_LABELS[stage] ?? stage} 记录已保存`);
      onClose();
    } catch {
      toast.error("保存失败，请重试");
    } finally {
      setIsSaving(false);
    }
  };

  const stageLabel = STAGE_LABELS[stage] ?? stage;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-surface-base rounded-2xl shadow-xl w-full max-w-lg mx-4 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <h2 className="text-base font-semibold text-text-main">
              记录 {stageLabel} 情况
            </h2>
            <p className="text-xs text-text-muted mt-0.5">
              记录这轮面试的题目和你的回答，便于后续 AI 复盘
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-main transition-colors p-1 rounded-lg hover:bg-surface-alt"
          >
            <XIcon className="w-4 h-4" strokeWidth={1.5} />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 px-5 py-4 space-y-4">
          <div>
            <p className="text-xs font-medium text-text-muted mb-2 uppercase tracking-wide">
              面试题目
            </p>
            <div className="space-y-3">
              {questions.map((q, idx) => (
                <div key={q.key} className="bg-surface-alt rounded-xl p-3 space-y-2">
                  <div className="flex items-start gap-2">
                    <span className="text-xs text-text-muted mt-2 w-5 shrink-0 text-center">
                      {idx + 1}
                    </span>
                    <div className="flex-1 space-y-1.5">
                      <input
                        type="text"
                        placeholder="面试题目"
                        value={q.text}
                        onChange={(e) => updateRow(q.key, "text", e.target.value)}
                        className="w-full text-sm bg-surface-base border border-border rounded-lg px-3 py-1.5 text-text-main placeholder:text-text-muted/50 focus:outline-none focus:ring-1 focus:ring-primary/40"
                      />
                      <textarea
                        placeholder="我的回答（可选）"
                        value={q.answer}
                        onChange={(e) => updateRow(q.key, "answer", e.target.value)}
                        rows={2}
                        className="w-full text-sm bg-surface-base border border-border rounded-lg px-3 py-1.5 text-text-main placeholder:text-text-muted/50 focus:outline-none focus:ring-1 focus:ring-primary/40 resize-none"
                      />
                    </div>
                    {questions.length > 1 && (
                      <button
                        onClick={() => removeRow(q.key)}
                        className="text-text-muted hover:text-red-400 transition-colors mt-1.5 p-1 rounded"
                      >
                        <TrashIcon className="w-3.5 h-3.5" strokeWidth={1.5} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <button
              onClick={addRow}
              className="mt-2 flex items-center gap-1.5 text-xs text-text-muted hover:text-primary transition-colors py-1"
            >
              <PlusIcon className="w-3.5 h-3.5" strokeWidth={2} />
              添加题目
            </button>
          </div>

          <div>
            <p className="text-xs font-medium text-text-muted mb-2 uppercase tracking-wide">
              备注（可选）
            </p>
            <textarea
              placeholder="面试整体感受、面试官风格等…"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full text-sm bg-surface-alt border border-border rounded-xl px-3 py-2 text-text-main placeholder:text-text-muted/50 focus:outline-none focus:ring-1 focus:ring-primary/40 resize-none"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-5 py-4 border-t border-border">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-sm text-text-muted hover:text-text-main transition-colors rounded-lg hover:bg-surface-alt"
          >
            跳过
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-60"
          >
            {isSaving ? "保存中…" : "保存记录"}
          </button>
        </div>
      </div>
    </div>
  );
}
