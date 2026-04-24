"use client";
import { use, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { interviewsApi, Question, InterviewStatus } from "@/lib/api/interviews";
import { ReviewPanel } from "../components/ReviewPanel";
import { MacaronBadge } from "@/components/macaron/MacaronBadge";
import { MacaronCard } from "@/components/macaron/MacaronCard";
import {
  ArrowLeftIcon,
  BuildingIcon,
  CalendarIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  PlusIcon,
  TrashIcon,
} from "lucide-react";
import Link from "next/link";
import { formatDate } from "@/lib/utils";
import { toast } from "sonner";

const statusLabel: Record<string, string> = {
  applied: "已投递",
  written_test: "笔试",
  first_interview: "一面",
  second_interview: "二面",
  third_interview: "三面",
  fourth_interview: "四面",
  hr_interview: "HR 面",
  offer: "Offer",
  rejected: "拒绝",
};

const STAGE_ORDER: InterviewStatus[] = [
  "written_test",
  "first_interview",
  "second_interview",
  "third_interview",
  "fourth_interview",
  "hr_interview",
];

function QuestionItem({
  question,
  interviewId,
  onDeleted,
}: {
  question: Question;
  interviewId: string;
  onDeleted: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [answerDraft, setAnswerDraft] = useState(question.my_answer ?? "");
  const [editing, setEditing] = useState(false);
  const queryClient = useQueryClient();

  const updateMut = useMutation({
    mutationFn: (my_answer: string) =>
      interviewsApi.updateQuestion(interviewId, question.id, { my_answer }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interview-questions", interviewId] });
      setEditing(false);
      toast.success("已保存");
    },
  });

  const deleteMut = useMutation({
    mutationFn: () => interviewsApi.deleteQuestion(interviewId, question.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interview-questions", interviewId] });
      onDeleted();
    },
  });

  return (
    <div className="border border-border rounded-xl overflow-hidden">
      <div
        className="flex items-start gap-2 px-3 py-2.5 bg-surface-alt cursor-pointer select-none"
        onClick={() => setExpanded((v) => !v)}
      >
        <span className="mt-0.5 text-text-muted/60 shrink-0">
          {expanded ? (
            <ChevronDownIcon className="w-3.5 h-3.5" strokeWidth={2} />
          ) : (
            <ChevronRightIcon className="w-3.5 h-3.5" strokeWidth={2} />
          )}
        </span>
        <p className="text-sm text-text-main flex-1">{question.question_text}</p>
        <button
          onClick={(e) => {
            e.stopPropagation();
            deleteMut.mutate();
          }}
          className="text-text-muted/50 hover:text-red-400 transition-colors p-0.5 rounded shrink-0"
        >
          <TrashIcon className="w-3.5 h-3.5" strokeWidth={1.5} />
        </button>
      </div>

      {expanded && (
        <div className="px-3 py-2.5 bg-surface-base border-t border-border space-y-2">
          <p className="text-xs font-medium text-text-muted">我的回答</p>
          {editing ? (
            <>
              <textarea
                value={answerDraft}
                onChange={(e) => setAnswerDraft(e.target.value)}
                rows={4}
                className="w-full text-sm bg-surface-alt border border-border rounded-lg px-3 py-2 text-text-main focus:outline-none focus:ring-1 focus:ring-primary/40 resize-none"
              />
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setEditing(false)}
                  className="text-xs text-text-muted hover:text-text-main transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={() => updateMut.mutate(answerDraft)}
                  disabled={updateMut.isPending}
                  className="text-xs bg-primary text-white px-3 py-1 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-60"
                >
                  保存
                </button>
              </div>
            </>
          ) : (
            <p
              className="text-sm text-text-muted whitespace-pre-wrap cursor-text hover:bg-surface-alt rounded-lg p-2 -mx-2 transition-colors min-h-[2rem]"
              onClick={() => setEditing(true)}
              title="点击编辑"
            >
              {question.my_answer || (
                <span className="italic opacity-50">暂无回答，点击填写</span>
              )}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function StageSection({
  stage,
  questions,
  interviewId,
  onAdd,
  onDeleted,
}: {
  stage: string;
  questions: Question[];
  interviewId: string;
  onAdd: () => void;
  onDeleted: () => void;
}) {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <div className="space-y-2">
      <div
        className="flex items-center gap-2 cursor-pointer"
        onClick={() => setCollapsed((v) => !v)}
      >
        {collapsed ? (
          <ChevronRightIcon className="w-3.5 h-3.5 text-text-muted" strokeWidth={2} />
        ) : (
          <ChevronDownIcon className="w-3.5 h-3.5 text-text-muted" strokeWidth={2} />
        )}
        <span className="text-xs font-semibold text-text-muted uppercase tracking-wide">
          {statusLabel[stage] ?? stage}
        </span>
        <span className="text-xs text-text-muted/60">({questions.length} 题)</span>
      </div>

      {!collapsed && (
        <div className="space-y-2 pl-5">
          {questions.map((q) => (
            <QuestionItem
              key={q.id}
              question={q}
              interviewId={interviewId}
              onDeleted={onDeleted}
            />
          ))}
          <button
            onClick={onAdd}
            className="flex items-center gap-1.5 text-xs text-text-muted hover:text-primary transition-colors py-1"
          >
            <PlusIcon className="w-3.5 h-3.5" strokeWidth={2} />
            添加题目
          </button>
        </div>
      )}
    </div>
  );
}

function AddQuestionInline({
  interviewId,
  stage,
  onDone,
}: {
  interviewId: string;
  stage: string;
  onDone: () => void;
}) {
  const [text, setText] = useState("");
  const [answer, setAnswer] = useState("");
  const queryClient = useQueryClient();

  const addMut = useMutation({
    mutationFn: () =>
      interviewsApi.addQuestion(interviewId, {
        question_text: text.trim(),
        my_answer: answer.trim() || undefined,
        category: stage,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interview-questions", interviewId] });
      toast.success("题目已添加");
      onDone();
    },
  });

  return (
    <div className="bg-surface-alt rounded-xl p-3 space-y-2 border border-border/60">
      <input
        autoFocus
        type="text"
        placeholder="面试题目"
        value={text}
        onChange={(e) => setText(e.target.value)}
        className="w-full text-sm bg-surface-base border border-border rounded-lg px-3 py-1.5 text-text-main placeholder:text-text-muted/50 focus:outline-none focus:ring-1 focus:ring-primary/40"
      />
      <textarea
        placeholder="我的回答（可选）"
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        rows={2}
        className="w-full text-sm bg-surface-base border border-border rounded-lg px-3 py-1.5 text-text-main placeholder:text-text-muted/50 focus:outline-none focus:ring-1 focus:ring-primary/40 resize-none"
      />
      <div className="flex gap-2 justify-end">
        <button
          onClick={onDone}
          className="text-xs text-text-muted hover:text-text-main transition-colors"
        >
          取消
        </button>
        <button
          onClick={() => addMut.mutate()}
          disabled={!text.trim() || addMut.isPending}
          className="text-xs bg-primary text-white px-3 py-1 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-60"
        >
          保存
        </button>
      </div>
    </div>
  );
}

export default function InterviewDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const queryClient = useQueryClient();
  const [addingStage, setAddingStage] = useState<string | null>(null);

  const { data: interview, isLoading } = useQuery({
    queryKey: ["interview", id],
    queryFn: () => interviewsApi.get(id),
  });

  const { data: questions = [] } = useQuery({
    queryKey: ["interview-questions", id],
    queryFn: () => interviewsApi.listQuestions(id),
    enabled: !!interview,
  });

  if (isLoading) {
    return (
      <div className="p-6 text-center text-text-muted text-sm py-16">
        加载中…
      </div>
    );
  }

  if (!interview) {
    return (
      <div className="p-6 text-center text-text-muted text-sm py-16">
        面试记录不存在
      </div>
    );
  }

  // Group questions by stage (category)
  const questionsByStage: Record<string, Question[]> = {};
  for (const q of questions) {
    const stage = q.category ?? "other";
    if (!questionsByStage[stage]) questionsByStage[stage] = [];
    questionsByStage[stage].push(q);
  }

  // Sort stages by predefined order, then any extra stages
  const orderedStages = [
    ...STAGE_ORDER.filter((s) => questionsByStage[s]),
    ...Object.keys(questionsByStage).filter((s) => !STAGE_ORDER.includes(s as InterviewStatus)),
  ];

  // Stages to show in "add questions" section — based on current status or all
  const availableStages: InterviewStatus[] = [
    "written_test",
    "first_interview",
    "second_interview",
    "third_interview",
    "fourth_interview",
    "hr_interview",
  ];

  return (
    <div className="p-6 max-w-2xl">
      <Link
        href="/interviews"
        className="flex items-center gap-1.5 text-text-muted text-sm mb-5 hover:text-text-main transition-colors"
      >
        <ArrowLeftIcon className="w-4 h-4" strokeWidth={1.5} />
        返回看板
      </Link>

      <MacaronCard className="mb-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-lg font-bold text-text-main">
              {interview.position}
            </h1>
            <div className="flex items-center gap-1.5 mt-1 text-text-muted text-sm">
              <BuildingIcon className="w-4 h-4" strokeWidth={1.5} />
              {interview.company_name}
            </div>
            {interview.interview_date && (
              <div className="flex items-center gap-1.5 mt-1 text-text-muted text-sm">
                <CalendarIcon className="w-4 h-4" strokeWidth={1.5} />
                {formatDate(interview.interview_date)}
              </div>
            )}
          </div>
          <MacaronBadge
            label={statusLabel[interview.status] ?? interview.status}
            variant={interview.status as "applied" | "written_test" | "first_interview" | "second_interview" | "third_interview" | "fourth_interview" | "hr_interview" | "offer" | "rejected"}
          />
        </div>

        {interview.notes && (
          <div className="mt-4 pt-4 border-t border-border">
            <p className="text-sm text-text-muted whitespace-pre-wrap">
              {interview.notes}
            </p>
          </div>
        )}

        <p className="text-xs text-text-muted mt-3">
          创建于 {formatDate(interview.created_at)}
        </p>
      </MacaronCard>

      {/* Questions by stage */}
      <MacaronCard className="mb-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-text-main">面试题目记录</h2>
          {!addingStage && (
            <div className="relative group">
              <button className="flex items-center gap-1 text-xs text-text-muted hover:text-primary transition-colors py-1 px-2 rounded-lg hover:bg-surface-alt">
                <PlusIcon className="w-3.5 h-3.5" strokeWidth={2} />
                添加
              </button>
              <div className="absolute right-0 top-full mt-1 bg-surface-base border border-border rounded-xl shadow-lg py-1 z-10 min-w-[110px] hidden group-hover:block">
                {availableStages.map((s) => (
                  <button
                    key={s}
                    onClick={() => setAddingStage(s)}
                    className="w-full text-left px-3 py-1.5 text-xs text-text-main hover:bg-surface-alt transition-colors"
                  >
                    {statusLabel[s]}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {orderedStages.length === 0 && !addingStage && (
          <p className="text-sm text-text-muted text-center py-6">
            暂无题目记录。拖动卡片到面试阶段后可快速添加，或点击右上角「添加」按钮手动录入。
          </p>
        )}

        <div className="space-y-5">
          {orderedStages.map((stage) => (
            <div key={stage}>
              <StageSection
                stage={stage}
                questions={questionsByStage[stage]}
                interviewId={id}
                onAdd={() => setAddingStage(stage)}
                onDeleted={() =>
                  queryClient.invalidateQueries({ queryKey: ["interview-questions", id] })
                }
              />
              {addingStage === stage && (
                <div className="mt-2 pl-5">
                  <AddQuestionInline
                    interviewId={id}
                    stage={stage}
                    onDone={() => setAddingStage(null)}
                  />
                </div>
              )}
            </div>
          ))}

          {addingStage && !orderedStages.includes(addingStage) && (
            <div>
              <p className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">
                {statusLabel[addingStage] ?? addingStage}
              </p>
              <div className="pl-5">
                <AddQuestionInline
                  interviewId={id}
                  stage={addingStage}
                  onDone={() => setAddingStage(null)}
                />
              </div>
            </div>
          )}
        </div>
      </MacaronCard>

      <ReviewPanel interviewId={id} />
    </div>
  );
}
