"use client";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Objective, okrApi } from "@/lib/api/okr";
import { MacaronCard } from "@/components/macaron/MacaronCard";
import { KRProgressBar } from "./KRProgressBar";
import { RadialBarChart, RadialBar, ResponsiveContainer } from "recharts";
import { ChevronDownIcon, ChevronRightIcon, PlusIcon, SparklesIcon } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface OKRTreeProps {
  objectives: Objective[];
}

interface KRFormState {
  title: string;
  target: string;
  unit: string;
}

export function OKRTree({ objectives }: OKRTreeProps) {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState<Set<string>>(new Set(objectives.map((o) => o.id)));
  const [addingKRFor, setAddingKRFor] = useState<string | null>(null);
  const [krForm, setKRForm] = useState<KRFormState>({ title: "", target: "", unit: "" });

  const suggestMutation = useMutation({
    mutationFn: (objectiveId: string) => okrApi.suggestTasks(objectiveId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["daily_tasks"] });
      toast.success("AI 任务建议已添加到今日任务");
    },
    onError: () => toast.error("获取 AI 建议失败"),
  });

  const addKRMutation = useMutation({
    mutationFn: ({ objectiveId, form }: { objectiveId: string; form: KRFormState }) =>
      okrApi.createKR(objectiveId, {
        title: form.title,
        target: parseFloat(form.target) || 1,
        unit: form.unit || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["objectives"] });
      setAddingKRFor(null);
      setKRForm({ title: "", target: "", unit: "" });
      toast.success("KR 已添加");
    },
    onError: () => toast.error("添加失败，请重试"),
  });

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const startAddKR = (objId: string) => {
    setKRForm({ title: "", target: "", unit: "" });
    setAddingKRFor(objId);
    setExpanded((prev) => new Set([...prev, objId]));
  };

  if (objectives.length === 0) {
    return (
      <div className="text-center text-text-muted text-sm py-16">
        暂无 OKR，点击「添加目标」开始规划
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {objectives.map((obj) => {
        const isExpanded = expanded.has(obj.id);
        const pct = Math.round(obj.progress * 100);
        const chartData = [{ value: pct, fill: "var(--color-macaron-mint)" }];

        return (
          <MacaronCard key={obj.id} accent="mint">
            {/* Objective 头部 */}
            <div
              className="flex items-center gap-3 cursor-pointer"
              onClick={() => toggle(obj.id)}
            >
              <div className="w-12 h-12 flex-shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart
                    cx="50%"
                    cy="50%"
                    innerRadius="60%"
                    outerRadius="100%"
                    data={chartData}
                    startAngle={90}
                    endAngle={90 - 360 * (pct / 100)}
                  >
                    <RadialBar dataKey="value" cornerRadius={4} />
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-text-main text-sm">{obj.title}</p>
                <p className="text-text-muted text-xs">
                  {obj.quarter} · {pct}% 完成
                </p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    suggestMutation.mutate(obj.id);
                  }}
                  disabled={suggestMutation.isPending}
                  className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-text-muted hover:bg-macaron-lilac/30 hover:text-text-main transition-colors disabled:opacity-50"
                >
                  <SparklesIcon className="w-3.5 h-3.5" strokeWidth={1.5} />
                  AI 建议
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    startAddKR(obj.id);
                  }}
                  className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-text-muted hover:bg-macaron-mint/30 hover:text-text-main transition-colors"
                >
                  <PlusIcon className="w-3.5 h-3.5" strokeWidth={1.5} />
                  添加 KR
                </button>
                {isExpanded ? (
                  <ChevronDownIcon className="w-4 h-4 text-text-muted" strokeWidth={1.5} />
                ) : (
                  <ChevronRightIcon className="w-4 h-4 text-text-muted" strokeWidth={1.5} />
                )}
              </div>
            </div>

            {/* KR 列表 */}
            {isExpanded && obj.key_results.length > 0 && (
              <div className={cn("mt-4 pt-4 border-t border-border space-y-1", "animate-fade-in")}>
                {obj.key_results.map((kr) => (
                  <KRProgressBar key={kr.id} kr={kr} />
                ))}
              </div>
            )}

            {isExpanded && obj.key_results.length === 0 && addingKRFor !== obj.id && (
              <p className="mt-3 text-text-muted text-xs text-center pt-3 border-t border-border">
                暂无 KR，点击「添加 KR」拆解目标
              </p>
            )}

            {/* 内联 KR 创建表单 */}
            {addingKRFor === obj.id && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  addKRMutation.mutate({ objectiveId: obj.id, form: krForm });
                }}
                className="mt-3 pt-3 border-t border-border animate-fade-in"
              >
                <p className="text-xs text-text-muted font-medium mb-2">新增关键结果</p>
                <div className="flex items-center gap-2">
                  <input
                    required
                    autoFocus
                    placeholder="KR 描述，例如：完成 5 个项目"
                    value={krForm.title}
                    onChange={(e) => setKRForm({ ...krForm, title: e.target.value })}
                    className="flex-1 px-3 py-1.5 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-mint/50"
                  />
                  <input
                    type="number"
                    min="0"
                    placeholder="目标值"
                    value={krForm.target}
                    onChange={(e) => setKRForm({ ...krForm, target: e.target.value })}
                    className="w-20 px-2 py-1.5 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-mint/50"
                  />
                  <input
                    placeholder="单位"
                    value={krForm.unit}
                    onChange={(e) => setKRForm({ ...krForm, unit: e.target.value })}
                    className="w-16 px-2 py-1.5 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-mint/50"
                  />
                </div>
                <div className="flex gap-2 mt-2">
                  <button
                    type="submit"
                    disabled={addKRMutation.isPending}
                    className="px-3 py-1.5 rounded-md bg-macaron-mint text-text-main text-xs font-medium transition-colors disabled:opacity-60"
                  >
                    {addKRMutation.isPending ? "添加中…" : "确认"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setAddingKRFor(null)}
                    className="px-3 py-1.5 rounded-md border border-border text-text-muted text-xs hover:bg-macaron-mint/10 transition-colors"
                  >
                    取消
                  </button>
                </div>
              </form>
            )}
          </MacaronCard>
        );
      })}
    </div>
  );
}
