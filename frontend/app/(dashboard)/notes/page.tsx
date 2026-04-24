"use client";
import { useQuery } from "@tanstack/react-query";
import { notesApi } from "@/lib/api/notes";
import { DailyCalendar } from "./components/DailyCalendar";
import { MacaronCard } from "@/components/macaron/MacaronCard";
import { todayStr, formatDate } from "@/lib/utils";
import Link from "next/link";
import { PlusIcon, BookOpenIcon } from "lucide-react";
import { format } from "date-fns";

export default function NotesPage() {
  const today = todayStr();
  const monthStr = format(new Date(), "yyyy-MM");

  const { data: notes = [], isLoading } = useQuery({
    queryKey: ["notes_month", monthStr],
    queryFn: () => notesApi.listByMonth(monthStr),
  });

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-text-main">学习笔记</h1>
          <p className="text-text-muted text-sm mt-0.5">
            本月 {notes.length} 篇笔记
          </p>
        </div>
        <Link
          href={`/notes/${today}`}
          className="flex items-center gap-1.5 px-4 py-2 rounded-md bg-macaron-lilac text-text-main text-sm font-medium hover:bg-[--color-accent-dark] transition-colors"
        >
          <PlusIcon className="w-4 h-4" strokeWidth={1.5} />
          今天的笔记
        </Link>
      </div>

      <div className="flex gap-6">
        {/* 月历 */}
        <div className="w-64 flex-shrink-0">
          <MacaronCard>
            <DailyCalendar />
          </MacaronCard>
        </div>

        {/* 笔记列表 */}
        <div className="flex-1 min-w-0">
          {isLoading ? (
            <p className="text-text-muted text-sm text-center py-16">加载中…</p>
          ) : notes.length === 0 ? (
            <div className="text-center py-16">
              <BookOpenIcon
                className="w-10 h-10 text-border mx-auto mb-3"
                strokeWidth={1}
              />
              <p className="text-text-muted text-sm">本月暂无笔记</p>
              <Link
                href={`/notes/${today}`}
                className="inline-block mt-3 text-sm text-text-main underline"
              >
                写下今天的第一篇
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {notes
                .sort((a, b) => b.date.localeCompare(a.date))
                .map((note) => (
                  <Link key={note.date} href={`/notes/${note.date}`}>
                    <MacaronCard
                      accent="lilac"
                      className="cursor-pointer hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-sm text-text-main truncate">
                            {note.title}
                          </p>
                          <p className="text-text-muted text-xs mt-0.5">
                            {formatDate(note.date)} · {note.word_count} 字
                          </p>
                          {note.tags.length > 0 && (
                            <div className="flex gap-1 mt-1.5 flex-wrap">
                              {note.tags.slice(0, 4).map((tag) => (
                                <span
                                  key={tag}
                                  className="text-xs bg-macaron-lilac/30 px-1.5 py-0.5 rounded-full text-text-main"
                                >
                                  #{tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </MacaronCard>
                  </Link>
                ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
