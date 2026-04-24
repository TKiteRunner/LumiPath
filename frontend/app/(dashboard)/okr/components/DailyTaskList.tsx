"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { okrApi } from "@/lib/api/okr";
import { todayStr } from "@/lib/utils";
import { toast } from "sonner";
import { CheckCircleIcon, CircleIcon } from "lucide-react";

export function DailyTaskList() {
  const queryClient = useQueryClient();
  const today = todayStr();

  const { data: tasks = [] } = useQuery({
    queryKey: ["daily_tasks", today],
    queryFn: () => okrApi.listTasks(today),
  });

  const completeMutation = useMutation({
    mutationFn: (taskId: string) => okrApi.completeTask(taskId),
    onMutate: async (taskId) => {
      await queryClient.cancelQueries({ queryKey: ["daily_tasks", today] });
      const prev = queryClient.getQueryData(["daily_tasks", today]);
      queryClient.setQueryData(
        ["daily_tasks", today],
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (old: any[]) => old?.map((t) => (t.id === taskId ? { ...t, completed: true } : t))
      );
      return { prev };
    },
    onError: (_err, _vars, context) => {
      if (context?.prev) queryClient.setQueryData(["daily_tasks", today], context.prev);
      toast.error("操作失败");
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["daily_tasks", today] }),
  });

  if (tasks.length === 0) {
    return (
      <p className="text-text-muted text-xs py-3 text-center">
        今日暂无任务
      </p>
    );
  }

  return (
    <ul className="space-y-1.5">
      {tasks.map((task) => (
        <li key={task.id} className="flex items-center gap-2">
          <button
            onClick={() => !task.completed && completeMutation.mutate(task.id)}
            disabled={task.completed}
            className="flex-shrink-0"
          >
            {task.completed ? (
              <CheckCircleIcon className="w-4 h-4 text-macaron-mint" strokeWidth={1.5} />
            ) : (
              <CircleIcon className="w-4 h-4 text-border hover:text-macaron-mint transition-colors" strokeWidth={1.5} />
            )}
          </button>
          <span
            className={`text-sm ${task.completed ? "line-through text-text-muted" : "text-text-main"}`}
          >
            {task.title}
          </span>
        </li>
      ))}
    </ul>
  );
}
