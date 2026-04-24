"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { okrApi } from "@/lib/api/okr";
import { OKRTree } from "./components/OKRTree";
import { DailyTaskList } from "./components/DailyTaskList";
import { MacaronCard } from "@/components/macaron/MacaronCard";
import { PlusIcon, TrashIcon } from "lucide-react";
import { toast } from "sonner";

interface KRDraft {
  title: string;
  target: string;
  unit: string;
}

const todayStr = () => new Date().toISOString().split("T")[0];

export default function OKRPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    title: "",
    startDate: todayStr(),
    endDate: todayStr(),
    krs: [] as KRDraft[],
  });

  const { data: objectives = [], isLoading } = useQuery({
    queryKey: ["objectives"],
    queryFn: okrApi.listObjectives,
  });

  const createMutation = useMutation({
    mutationFn: async (payload: typeof form) => {
      const quarter = `${payload.startDate} 到 ${payload.endDate}`;
      const obj = await okrApi.createObjective({ title: payload.title, quarter });
      await Promise.all(
        payload.krs
          .filter((kr) => kr.title.trim())
          .map((kr) =>
            okrApi.createKR(obj.id, {
              title: kr.title,
              target: parseFloat(kr.target) || 1,
              unit: kr.unit || undefined,
            })
          )
      );
      return obj;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["objectives"] });
      setShowForm(false);
      setForm({ title: "", startDate: todayStr(), endDate: todayStr(), krs: [] });
      toast.success("OKR 目标已创建");
    },
    onError: () => toast.error("创建失败，请重试"),
  });

  const addKR = () =>
    setForm((f) => ({ ...f, krs: [...f.krs, { title: "", target: "", unit: "" }] }));

  const removeKR = (i: number) =>
    setForm((f) => ({ ...f, krs: f.krs.filter((_, idx) => idx !== i) }));

  const updateKR = (i: number, field: keyof KRDraft, value: string) =>
    setForm((f) => {
      const krs = [...f.krs];
      krs[i] = { ...krs[i], [field]: value };
      return { ...f, krs };
    });

  return (
    <div className="p-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-text-main">OKR 规划</h1>
          <p className="text-text-muted text-sm mt-0.5">量化目标，追踪成长</p>
        </div>
        <button
          onClick={() => {
            setForm({ title: "", startDate: todayStr(), endDate: todayStr(), krs: [] });
            setShowForm(true);
          }}
          className="flex items-center gap-1.5 px-4 py-2 rounded-md bg-macaron-mint text-text-main text-sm font-medium hover:bg-[--color-secondary-dark] transition-colors"
        >
          <PlusIcon className="w-4 h-4" strokeWidth={1.5} />
          添加目标
        </button>
      </div>

      <div className="flex gap-6">
        <div className="flex-1 min-w-0">
          {showForm && (
            <MacaronCard className="mb-4 max-w-lg">
              <h3 className="font-semibold text-text-main text-sm mb-3">新建目标</h3>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  createMutation.mutate(form);
                }}
                className="space-y-3"
              >
                <input
                  required
                  placeholder="目标描述，例如：成为全栈工程师"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="w-full px-3 py-2 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-mint/50"
                />

                {/* 日期范围选择 */}
                <div className="flex items-end gap-2">
                  <div className="flex-1">
                    <label className="text-xs text-text-muted mb-1 block">开始日期</label>
                    <input
                      type="date"
                      required
                      value={form.startDate}
                      onChange={(e) => setForm({ ...form, startDate: e.target.value })}
                      className="w-full px-3 py-2 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-mint/50"
                    />
                  </div>
                  <span className="text-text-muted text-sm pb-2">至</span>
                  <div className="flex-1">
                    <label className="text-xs text-text-muted mb-1 block">结束日期</label>
                    <input
                      type="date"
                      required
                      value={form.endDate}
                      min={form.startDate}
                      onChange={(e) => setForm({ ...form, endDate: e.target.value })}
                      className="w-full px-3 py-2 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-mint/50"
                    />
                  </div>
                </div>

                {/* KR 子任务列表 */}
                {form.krs.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs text-text-muted font-medium">关键结果 (KR)</p>
                    {form.krs.map((kr, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <input
                          placeholder={`KR ${i + 1}，例如：完成 5 个项目`}
                          value={kr.title}
                          onChange={(e) => updateKR(i, "title", e.target.value)}
                          className="flex-1 px-3 py-1.5 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-mint/50"
                        />
                        <input
                          type="number"
                          min="0"
                          placeholder="目标值"
                          value={kr.target}
                          onChange={(e) => updateKR(i, "target", e.target.value)}
                          className="w-20 px-2 py-1.5 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-mint/50"
                        />
                        <input
                          placeholder="单位"
                          value={kr.unit}
                          onChange={(e) => updateKR(i, "unit", e.target.value)}
                          className="w-16 px-2 py-1.5 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-mint/50"
                        />
                        <button
                          type="button"
                          onClick={() => removeKR(i)}
                          className="text-text-muted hover:text-macaron-peach transition-colors flex-shrink-0"
                        >
                          <TrashIcon className="w-4 h-4" strokeWidth={1.5} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <button
                  type="button"
                  onClick={addKR}
                  className="flex items-center gap-1 text-xs text-text-muted hover:text-text-main transition-colors"
                >
                  <PlusIcon className="w-3.5 h-3.5" strokeWidth={1.5} />
                  添加关键结果 (KR)
                </button>

                <div className="flex gap-2 pt-1">
                  <button
                    type="submit"
                    disabled={createMutation.isPending}
                    className="px-4 py-2 rounded-md bg-macaron-mint text-text-main text-sm font-medium transition-colors disabled:opacity-60"
                  >
                    {createMutation.isPending ? "创建中…" : "确认"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-4 py-2 rounded-md border border-border text-text-muted text-sm hover:bg-macaron-mint/10 transition-colors"
                  >
                    取消
                  </button>
                </div>
              </form>
            </MacaronCard>
          )}

          {isLoading ? (
            <p className="text-text-muted text-sm text-center py-16">加载中…</p>
          ) : (
            <OKRTree objectives={objectives} />
          )}
        </div>

        <div className="w-56 flex-shrink-0">
          <MacaronCard accent="sky">
            <h3 className="font-semibold text-text-main text-sm mb-3">今日任务</h3>
            <DailyTaskList />
          </MacaronCard>
        </div>
      </div>
    </div>
  );
}
