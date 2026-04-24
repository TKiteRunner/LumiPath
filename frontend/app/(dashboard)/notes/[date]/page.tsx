"use client";
import { use, useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notesApi } from "@/lib/api/notes";
import { MilkdownEditor } from "../components/MilkdownEditor";
import { BacklinksPanel } from "../components/BacklinksPanel";
import { DailyCalendar } from "../components/DailyCalendar";
import { MacaronCard } from "@/components/macaron/MacaronCard";
import { ArrowLeftIcon, CheckIcon } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { formatDate } from "@/lib/utils";

export default function NoteDetailPage({
  params,
}: {
  params: Promise<{ date: string }>;
}) {
  const { date } = use(params);
  const queryClient = useQueryClient();
  const [savedIndicator, setSavedIndicator] = useState(false);

  const { data: note, isLoading } = useQuery({
    queryKey: ["note", date],
    queryFn: () => notesApi.getByDate(date),
    retry: false,
  });

  const saveMutation = useMutation({
    mutationFn: (content: string) => notesApi.upsert(date, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notes_month"] });
      queryClient.invalidateQueries({ queryKey: ["note", date] });
      setSavedIndicator(true);
      setTimeout(() => setSavedIndicator(false), 2000);
    },
    onError: () => toast.error("保存失败，请检查网络"),
  });

  const initialContent =
    note?.content ??
    `---\ndate: ${date}\ntags: []\n---\n\n# ${formatDate(date)} 学习日志\n\n## 🎯 今日目标\n- [ ] \n\n## 📚 学习内容\n\n## 🧠 复盘\n\n## 💡 明日计划\n`;

  return (
    <div className="flex h-screen">
      {/* 左侧日历 */}
      <div className="w-52 flex-shrink-0 border-r border-border bg-white p-4 overflow-y-auto">
        <DailyCalendar selectedDate={date} />
      </div>

      {/* 主编辑区 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 顶部导航栏 */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-white">
          <div className="flex items-center gap-3">
            <Link
              href="/notes"
              className="flex items-center gap-1.5 text-text-muted text-sm hover:text-text-main transition-colors"
            >
              <ArrowLeftIcon className="w-4 h-4" strokeWidth={1.5} />
              笔记
            </Link>
            <span className="text-text-muted">/</span>
            <span className="text-sm text-text-main font-medium">
              {formatDate(date)}
            </span>
          </div>

          {savedIndicator && (
            <span className="flex items-center gap-1 text-xs text-macaron-mint font-medium animate-fade-in">
              <CheckIcon className="w-3.5 h-3.5" strokeWidth={2} />
              已保存
            </span>
          )}
        </div>

        {/* 编辑器 */}
        <div className="flex-1 overflow-y-auto px-8 py-6">
          {isLoading ? (
            <p className="text-text-muted text-sm">加载中…</p>
          ) : (
            <MilkdownEditor
              content={initialContent}
              onChange={(md) => saveMutation.mutate(md)}
            />
          )}
        </div>
      </div>

      {/* 右侧面板：反向链接 + 标签 */}
      <div className="w-56 flex-shrink-0 border-l border-border bg-white p-4 overflow-y-auto">
        <BacklinksPanel date={date} />
      </div>
    </div>
  );
}
