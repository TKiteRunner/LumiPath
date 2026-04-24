"use client";
import {
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  getDay,
  format,
  isSameDay,
  addMonths,
  subMonths,
} from "date-fns";
import { zhCN } from "date-fns/locale";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { notesApi } from "@/lib/api/notes";
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";

const WEEKDAYS = ["日", "一", "二", "三", "四", "五", "六"];

export function DailyCalendar({ selectedDate }: { selectedDate?: string }) {
  const router = useRouter();
  const [viewDate, setViewDate] = useState(() => new Date());

  const monthStr = format(viewDate, "yyyy-MM");

  const { data: notes = [] } = useQuery({
    queryKey: ["notes_month", monthStr],
    queryFn: () => notesApi.listByMonth(monthStr),
  });

  const noteSet = new Set(notes.map((n) => n.date));

  const firstDay = startOfMonth(viewDate);
  const lastDay = endOfMonth(viewDate);
  const days = eachDayOfInterval({ start: firstDay, end: lastDay });
  const startPad = getDay(firstDay);
  const paddedDays: (Date | null)[] = [
    ...Array(startPad).fill(null),
    ...days,
  ];

  const handleDayClick = (day: Date) => {
    router.push(`/notes/${format(day, "yyyy-MM-dd")}`);
  };

  return (
    <div>
      {/* 月份导航 */}
      <div className="flex items-center justify-between mb-3">
        <button
          onClick={() => setViewDate(subMonths(viewDate, 1))}
          className="p-1 rounded-md hover:bg-macaron-pink/10 transition-colors"
        >
          <ChevronLeftIcon className="w-4 h-4 text-text-muted" strokeWidth={1.5} />
        </button>
        <span className="text-sm font-semibold text-text-main">
          {format(viewDate, "yyyy 年 M 月", { locale: zhCN })}
        </span>
        <button
          onClick={() => setViewDate(addMonths(viewDate, 1))}
          className="p-1 rounded-md hover:bg-macaron-pink/10 transition-colors"
        >
          <ChevronRightIcon className="w-4 h-4 text-text-muted" strokeWidth={1.5} />
        </button>
      </div>

      {/* 星期头 */}
      <div className="grid grid-cols-7 mb-1">
        {WEEKDAYS.map((w) => (
          <div
            key={w}
            className="text-center text-xs text-text-muted font-medium py-1"
          >
            {w}
          </div>
        ))}
      </div>

      {/* 日期格 */}
      <div className="grid grid-cols-7 gap-0.5">
        {paddedDays.map((day, idx) => {
          if (!day) return <div key={`pad-${idx}`} />;
          const dateStr = format(day, "yyyy-MM-dd");
          const hasNote = noteSet.has(dateStr);
          const isSelected = selectedDate === dateStr;
          const isToday = isSameDay(day, new Date());

          return (
            <button
              key={dateStr}
              onClick={() => handleDayClick(day)}
              className={cn(
                "relative flex flex-col items-center justify-center h-9 w-full rounded-md text-xs transition-colors",
                isSelected
                  ? "bg-macaron-pink text-text-main font-semibold"
                  : isToday
                  ? "bg-macaron-lemon/60 font-semibold text-text-main"
                  : "hover:bg-macaron-pink/10 text-text-main"
              )}
            >
              {format(day, "d")}
              {hasNote && (
                <span
                  className={cn(
                    "absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full",
                    isSelected ? "bg-text-main" : "bg-macaron-mint"
                  )}
                />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
