"use client";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Interview } from "@/lib/api/interviews";
import { MacaronCard } from "@/components/macaron/MacaronCard";
import { MacaronBadge } from "@/components/macaron/MacaronBadge";
import { BuildingIcon, CalendarIcon } from "lucide-react";
import Link from "next/link";
import { formatDate } from "@/lib/utils";

const statusAccent: Record<string, "pink" | "mint" | "lemon" | "lilac" | "sky" | "peach"> = {
  applied: "sky",
  written_test: "lemon",
  first_interview: "peach",
  second_interview: "peach",
  third_interview: "peach",
  fourth_interview: "peach",
  hr_interview: "lilac",
  offer: "mint",
  rejected: "pink",
};

const statusLabel: Record<string, string> = {
  applied: "已投递",
  written_test: "笔试",
  first_interview: "一面",
  second_interview: "二面",
  third_interview: "三面",
  fourth_interview: "四面",
  hr_interview: "HR 面",
  offer: "Offer",
  rejected: "拒绝",
};

export function InterviewCard({ interview }: { interview: Interview }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: interview.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <Link href={`/interviews/${interview.id}`}>
        <MacaronCard
          accent={statusAccent[interview.status]}
          className="cursor-grab active:cursor-grabbing mb-2 hover:shadow-md"
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm text-text-main truncate">
                {interview.position}
              </p>
              <div className="flex items-center gap-1 mt-1 text-text-muted text-xs">
                <BuildingIcon className="w-3 h-3 flex-shrink-0" strokeWidth={1.5} />
                <span className="truncate">{interview.company_name}</span>
              </div>
              {interview.interview_date && (
                <div className="flex items-center gap-1 mt-1 text-text-muted text-xs">
                  <CalendarIcon className="w-3 h-3 flex-shrink-0" strokeWidth={1.5} />
                  <span>{formatDate(interview.interview_date)}</span>
                </div>
              )}
            </div>
            <MacaronBadge
              label={statusLabel[interview.status] ?? interview.status}
              variant={interview.status as "applied" | "written_test" | "first_interview" | "second_interview" | "third_interview" | "fourth_interview" | "hr_interview" | "offer" | "rejected"}
              className="flex-shrink-0"
            />
          </div>
        </MacaronCard>
      </Link>
    </div>
  );
}
