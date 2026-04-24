"use client";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { settingsApi } from "@/lib/api/settings";
import { toast } from "sonner";
import { EyeIcon, EyeOffIcon, ChevronDownIcon, ChevronRightIcon } from "lucide-react";
import { cn } from "@/lib/utils";

const PROVIDERS = [
  { value: "anthropic", label: "Anthropic (Claude)" },
  { value: "openai",    label: "OpenAI" },
  { value: "deepseek",  label: "DeepSeek" },
  { value: "qwen",      label: "通义千问 (Qwen)" },
  { value: "gemini",    label: "Google Gemini" },
  { value: "doubao",    label: "豆包 (Doubao)" },
  { value: "kimi",      label: "Kimi (Moonshot)" },
  { value: "minimax",   label: "MiniMax" },
  { value: "zhipu",     label: "智谱 AI (GLM)" },
];

const AGENTS = [
  { key: "interview", label: "面试 Agent" },
  { key: "notes", label: "笔记 Agent" },
  { key: "okr", label: "OKR Agent" },
  { key: "memory", label: "记忆 Agent" },
];

function PasswordInput({ value, onChange, placeholder }: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        type={show ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder ?? "sk-..."}
        className="w-full px-3 py-2 pr-9 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-lilac/50"
      />
      <button
        type="button"
        onClick={() => setShow((v) => !v)}
        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-main"
      >
        {show ? <EyeOffIcon className="w-3.5 h-3.5" strokeWidth={1.5} /> : <EyeIcon className="w-3.5 h-3.5" strokeWidth={1.5} />}
      </button>
    </div>
  );
}

export function ApiKeyForm() {
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);

  const { data: settings, isLoading } = useQuery({
    queryKey: ["llm_settings"],
    queryFn: settingsApi.getLLMSettings,
  });

  const [form, setForm] = useState({
    default_provider: settings?.default_provider ?? "anthropic",
    default_api_key: settings?.default_api_key ?? "",
    agent_assignments: settings?.agent_assignments ?? {},
  });

  const mutation = useMutation({
    mutationFn: settingsApi.updateLLMSettings,
    onSuccess: () => toast.success("LLM 设置已保存"),
    onError: () => toast.error("保存失败，请重试"),
  });

  if (isLoading)
    return <p className="text-text-muted text-sm">加载中…</p>;

  const updateAgent = (agentKey: string, field: string, val: string) => {
    setForm((prev) => ({
      ...prev,
      agent_assignments: {
        ...prev.agent_assignments,
        [agentKey]: {
          ...prev.agent_assignments[agentKey],
          [field]: val,
        },
      },
    }));
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate(form);
      }}
      className="space-y-5"
    >
      {/* 默认 Provider */}
      <div>
        <label className="block text-sm font-medium text-text-main mb-1.5">
          默认 LLM Provider
        </label>
        <select
          value={form.default_provider}
          onChange={(e) => setForm({ ...form, default_provider: e.target.value })}
          className="w-full max-w-xs px-3 py-2 rounded-md border border-border text-sm focus:outline-none focus:ring-2 focus:ring-macaron-lilac/50 bg-white"
        >
          {PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>
      </div>

      {/* 默认 API Key */}
      <div>
        <label className="block text-sm font-medium text-text-main mb-1.5">
          默认 API Key
        </label>
        <div className="max-w-sm">
          <PasswordInput
            value={form.default_api_key}
            onChange={(v) => setForm({ ...form, default_api_key: v })}
          />
        </div>
        <p className="text-xs text-text-muted mt-1">
          各 Agent 未单独配置时使用此 Key
        </p>
      </div>

      {/* 每 Agent 独立 Key */}
      <div>
        <p className="text-sm font-medium text-text-main mb-2">
          每个 Agent 独立配置（可选）
        </p>
        <div className="space-y-2 max-w-sm">
          {AGENTS.map(({ key, label }) => {
            const isOpen = expandedAgent === key;
            const assignment = form.agent_assignments[key] ?? { provider: "", api_key: "" };
            return (
              <div key={key} className="border border-border rounded-md overflow-hidden">
                <button
                  type="button"
                  onClick={() => setExpandedAgent(isOpen ? null : key)}
                  className="w-full flex items-center justify-between px-3 py-2.5 text-sm text-text-main hover:bg-macaron-lilac/10 transition-colors"
                >
                  {label}
                  {isOpen ? (
                    <ChevronDownIcon className="w-4 h-4 text-text-muted" strokeWidth={1.5} />
                  ) : (
                    <ChevronRightIcon className="w-4 h-4 text-text-muted" strokeWidth={1.5} />
                  )}
                </button>
                {isOpen && (
                  <div className="px-3 pb-3 space-y-2 border-t border-border bg-macaron-lilac/5">
                    <div className="mt-2">
                      <label className="block text-xs text-text-muted mb-1">Provider</label>
                      <select
                        value={assignment.provider}
                        onChange={(e) => updateAgent(key, "provider", e.target.value)}
                        className="w-full px-2.5 py-1.5 rounded border border-border text-xs bg-white focus:outline-none"
                      >
                        <option value="">使用默认</option>
                        {PROVIDERS.map((p) => (
                          <option key={p.value} value={p.value}>{p.label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-text-muted mb-1">API Key</label>
                      <PasswordInput
                        value={assignment.api_key}
                        onChange={(v) => updateAgent(key, "api_key", v)}
                        placeholder="留空则使用默认 Key"
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <button
        type="submit"
        disabled={mutation.isPending}
        className="px-5 py-2 rounded-md bg-macaron-lilac text-text-main text-sm font-medium hover:bg-[--color-accent-dark] transition-colors disabled:opacity-60"
      >
        {mutation.isPending ? "保存中…" : "保存设置"}
      </button>
    </form>
  );
}
