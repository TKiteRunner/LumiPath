"use client";
import { useState } from "react";
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import {
  Interview,
  InterviewStatus,
  interviewsApi,
} from "@/lib/api/interviews";
import { InterviewCard } from "./InterviewCard";
import { RoundRecordDialog } from "./RoundRecordDialog";
import { toast } from "sonner";

const COLUMNS: { key: InterviewStatus; label: string; color: string }[] = [
  { key: "applied", label: "已投递", color: "bg-macaron-sky/30" },
  { key: "written_test", label: "笔试", color: "bg-macaron-lemon/30" },
  { key: "first_interview", label: "一面", color: "bg-macaron-peach/30" },
  { key: "second_interview", label: "二面", color: "bg-macaron-peach/40" },
  { key: "third_interview", label: "三面", color: "bg-macaron-peach/50" },
  { key: "fourth_interview", label: "四面", color: "bg-macaron-peach/60" },
  { key: "hr_interview", label: "HR 面", color: "bg-macaron-lilac/30" },
  { key: "offer", label: "Offer ✨", color: "bg-macaron-mint/30" },
  { key: "rejected", label: "拒绝", color: "bg-macaron-pink/20" },
];

// Stages that should prompt the user to record questions after drag
const RECORDABLE_STAGES: InterviewStatus[] = [
  "written_test",
  "first_interview",
  "second_interview",
  "third_interview",
  "fourth_interview",
  "hr_interview",
];

interface PendingRecord {
  interviewId: string;
  stage: InterviewStatus;
}

export function KanbanBoard({ interviews }: { interviews: Interview[] }) {
  const queryClient = useQueryClient();
  const [pendingRecord, setPendingRecord] = useState<PendingRecord | null>(null);

  const updateStatus = useMutation({
    mutationFn: ({
      id,
      status,
    }: {
      id: string;
      status: InterviewStatus;
    }) => interviewsApi.updateStatus(id, status),
    onMutate: async ({ id, status }) => {
      await queryClient.cancelQueries({ queryKey: ["interviews"] });
      const previous = queryClient.getQueryData<Interview[]>(["interviews"]);
      queryClient.setQueryData<Interview[]>(["interviews"], (old) =>
        old?.map((i) => (i.id === id ? { ...i, status } : i)) ?? []
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["interviews"], context.previous);
      }
      toast.error("状态更新失败");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
    },
  });

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const draggedId = String(active.id);
    const targetColumnKey = String(over.id) as InterviewStatus;

    if (!COLUMNS.some((c) => c.key === targetColumnKey)) return;

    // Get the previous status before mutation
    const interview = interviews.find((i) => i.id === draggedId);
    if (interview?.status === targetColumnKey) return;

    updateStatus.mutate({ id: draggedId, status: targetColumnKey });

    // Prompt to record questions for meaningful stages
    if (RECORDABLE_STAGES.includes(targetColumnKey)) {
      setPendingRecord({ interviewId: draggedId, stage: targetColumnKey });
    }
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { over } = event;
    if (!over) return;
    const targetColumnKey = String(over.id) as InterviewStatus;
    if (!COLUMNS.some((c) => c.key === targetColumnKey)) return;
  };

  const byStatus = (status: InterviewStatus) =>
    interviews.filter((i) => i.status === status);

  return (
    <>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragEnd={handleDragEnd}
        onDragOver={handleDragOver}
      >
        <div className="flex gap-4 overflow-x-auto pb-4 min-h-[60vh]">
          {COLUMNS.map(({ key, label, color }) => (
            <div key={key} className={`flex-shrink-0 w-52 rounded-lg ${color} p-3`} id={key}>
              <h3 className="text-xs font-semibold text-text-muted mb-3 uppercase tracking-wide">
                {label}
                <span className="ml-1 text-text-muted/60">
                  ({byStatus(key).length})
                </span>
              </h3>
              <SortableContext
                items={byStatus(key).map((i) => i.id)}
                strategy={verticalListSortingStrategy}
              >
                {byStatus(key).map((interview) => (
                  <InterviewCard key={interview.id} interview={interview} />
                ))}
              </SortableContext>
            </div>
          ))}
        </div>
      </DndContext>

      {pendingRecord && (
        <RoundRecordDialog
          interviewId={pendingRecord.interviewId}
          stage={pendingRecord.stage}
          onClose={() => setPendingRecord(null)}
        />
      )}
    </>
  );
}
