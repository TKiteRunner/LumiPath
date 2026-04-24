"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { interviewsApi, CreateInterviewPayload } from "@/lib/api/interviews";
import { KanbanBoard } from "./components/KanbanBoard";
import { PlusIcon } from "lucide-react";

export default function InterviewsPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<CreateInterviewPayload>({
    company_name: "",
    position: "",
    round: 1,
    status: "applied",
  });

  const { data: interviews = [], isLoading } = useQuery({
    queryKey: ["interviews"],
    queryFn: interviewsApi.list,
  });

  const createMutation = useMutation({
    mutationFn: interviewsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
      setShowForm(false);
      setForm({ company_name: "", position: "", round: 1, status: "applied" });
      toast.success("面试记录已添加");
    },
    onError: () => toast.error("添加失败，请重试"),
  });

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-text-main">面试看板</h1>
          <p className="text-text-muted text-sm mt-0.5">
            共 {interviews.length} 条记录
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-md bg-macaron-pink text-text-main text-sm font-medium hover:bg-[--color-primary-dark] transition-colors"
        >
          <PlusIcon className="w-4 h-4" strokeWidth={1.5} />
          添加面试
        </button>
      </div>

      {/* 添加表单 */}
      {showForm && (
        <div className="macaron-card p-4 mb-6 max-w-md">
          <h3 className="font-semibold text-text-main text-sm mb-3">添加面试记录</h3>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createMutation.mutate(form);
            }}
            className="space-y-3"
          >
            <input
              required
              placeholder="公司名称"
              value={form.company_name}
              onChange={(e) => setForm({ ...form, company_name: e.target.value })}
              className="w-full px-3 py-2 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-pink/50"
            />
            <input
              required
              placeholder="职位名称"
              value={form.position}
              onChange={(e) => setForm({ ...form, position: e.target.value })}
              className="w-full px-3 py-2 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-pink/50"
            />
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="px-4 py-2 rounded-md bg-macaron-pink text-text-main text-sm font-medium hover:bg-[--color-primary-dark] transition-colors disabled:opacity-60"
              >
                {createMutation.isPending ? "添加中…" : "确认添加"}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 rounded-md border border-border text-text-muted text-sm hover:bg-macaron-pink/10 transition-colors"
              >
                取消
              </button>
            </div>
          </form>
        </div>
      )}

      {isLoading ? (
        <div className="text-center text-text-muted py-16 text-sm">
          加载中…
        </div>
      ) : interviews.length === 0 ? (
        <div className="text-center text-text-muted py-16 text-sm">
          暂无面试记录，点击「添加面试」开始
        </div>
      ) : (
        <KanbanBoard interviews={interviews} />
      )}
    </div>
  );
}
