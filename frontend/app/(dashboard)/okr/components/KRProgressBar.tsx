"use client";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { KeyResult, okrApi } from "@/lib/api/okr";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Pencil } from "lucide-react";

interface KRProgressBarProps {
  kr: KeyResult;
}

export function KRProgressBar({ kr }: KRProgressBarProps) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [inputVal, setInputVal] = useState(String(kr.current_value));

  const pct = Math.min(
    100,
    kr.target_value > 0
      ? Math.round((kr.current_value / kr.target_value) * 100)
      : 0
  );

  const updateMutation = useMutation({
    mutationFn: (val: number) => okrApi.updateKR(kr.id, { current_value: val }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["objectives"] });
      setEditing(false);
      toast.success("KR 进度已更新");
    },
    onError: () => toast.error("更新失败"),
  });

  const handleSave = () => {
    const val = parseFloat(inputVal);
    if (isNaN(val)) return;
    updateMutation.mutate(val);
  };

  const barColor =
    pct >= 100
      ? "bg-macaron-mint"
      : pct >= 60
      ? "bg-macaron-lemon"
      : "bg-macaron-peach";

  return (
    <div className="py-2">
      <div className="flex items-center justify-between mb-1">
        <p className="text-sm text-text-main flex-1 mr-2">{kr.title}</p>
        <div className="flex items-center gap-1.5 text-xs text-text-muted flex-shrink-0">
          {editing ? (
            <>
              <input
                type="number"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                className="w-16 px-1.5 py-0.5 rounded border border-border text-xs text-text-main focus:outline-none focus:ring-1 focus:ring-macaron-pink/50"
                onKeyDown={(e) => e.key === "Enter" && handleSave()}
                autoFocus
              />
              <span>/ {kr.target_value} {kr.unit}</span>
              <button
                onClick={handleSave}
                className="text-macaron-mint font-medium text-xs"
              >
                保存
              </button>
              <button onClick={() => setEditing(false)} className="text-text-muted text-xs">
                取消
              </button>
            </>
          ) : (
            <div className="flex items-center gap-1.5 group">
              <span>{kr.current_value} / {kr.target_value} {kr.unit}</span>
              <span
                className={cn(
                  "font-bold",
                  pct >= 100
                    ? "text-green-600"
                    : pct >= 60
                    ? "text-yellow-600"
                    : "text-text-muted"
                )}
              >
                {pct}%
              </span>
              <button
                onClick={() => {
                  setInputVal(String(kr.current_value));
                  setEditing(true);
                }}
                className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:bg-border"
                title="更新进度"
              >
                <Pencil className="w-3 h-3 text-text-muted" />
              </button>
            </div>
          )}
        </div>
      </div>
      <div className="h-1.5 bg-border rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all", barColor)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
