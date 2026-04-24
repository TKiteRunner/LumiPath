"use client";
import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { settingsApi } from "@/lib/api/settings";
import { toast } from "sonner";
import { RotateCcwIcon } from "lucide-react";

const AGENTS = [
  {
    key: "interview",
    label: "面试 Agent",
    description: "面试复盘、题目搜索、状态分析",
    defaultPrompt:
      "你是专业的面试教练（Interview Coach），帮助用户进行面试复盘、题目搜索与状态分析。请用中文回复。",
  },
  {
    key: "notes",
    label: "笔记 Agent",
    description: "日志管理、知识检索、周月总结",
    defaultPrompt:
      "你是学习笔记助手（Notes Assistant），帮助用户管理每日学习日志、检索知识库、生成周月总结。请用中文回复。",
  },
  {
    key: "okr",
    label: "OKR Agent",
    description: "目标制定、进度追踪、任务拆解",
    defaultPrompt:
      "你是 OKR 教练（OKR Coach），帮助用户制定目标、追踪进度、拆解每日任务和生成季度报告。请用中文回复。",
  },
  {
    key: "memory",
    label: "记忆 Agent",
    description: "历史记录召回、信息归纳总结",
    defaultPrompt:
      "你是记忆检索助手（Memory Assistant），专门帮助用户从历史记录中召回相关信息并进行总结归纳。请用中文回复。",
  },
];

export function AgentSkillsForm() {
  const { data, isLoading } = useQuery({
    queryKey: ["agent_skills"],
    queryFn: settingsApi.getAgentSkills,
  });

  const [skills, setSkills] = useState<Record<string, string>>({});

  useEffect(() => {
    if (data?.skills) setSkills(data.skills);
  }, [data]);

  const mutation = useMutation({
    mutationFn: () => settingsApi.updateAgentSkills({ skills }),
    onSuccess: () => toast.success("Skills 已保存"),
    onError: () => toast.error("保存失败，请重试"),
  });

  const handleReset = (agentKey: string, defaultPrompt: string) => {
    setSkills((prev) => ({ ...prev, [agentKey]: defaultPrompt }));
  };

  if (isLoading) return <p className="text-text-muted text-sm">加载中…</p>;

  return (
    <div className="space-y-4">
      <p className="text-xs text-text-muted">
        自定义每个 Agent 的系统提示词（System Prompt），Agent 会以此为角色定义来回复你。
      </p>

      {AGENTS.map(({ key, label, description, defaultPrompt }) => (
        <div key={key} className="space-y-1.5">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-medium text-text-main">{label}</span>
              <span className="ml-2 text-xs text-text-muted">{description}</span>
            </div>
            <button
              type="button"
              onClick={() => handleReset(key, defaultPrompt)}
              className="flex items-center gap-1 text-xs text-text-muted hover:text-text-main transition-colors px-1.5 py-0.5 rounded hover:bg-border"
              title="恢复默认"
            >
              <RotateCcwIcon className="w-3 h-3" strokeWidth={1.5} />
              恢复默认
            </button>
          </div>
          <textarea
            rows={12}
            value={skills[key] ?? defaultPrompt}
            onChange={(e) => setSkills((prev) => ({ ...prev, [key]: e.target.value }))}
            className="w-full px-3 py-2 rounded-md border border-border text-xs text-text-main font-mono leading-relaxed focus:outline-none focus:ring-2 focus:ring-macaron-lilac/50 resize-y bg-white"
          />
        </div>
      ))}

      <button
        type="button"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
        className="px-5 py-2 rounded-md bg-macaron-lilac text-text-main text-sm font-medium hover:bg-[--color-accent-dark] transition-colors disabled:opacity-60"
      >
        {mutation.isPending ? "保存中…" : "保存 Skills"}
      </button>
    </div>
  );
}
