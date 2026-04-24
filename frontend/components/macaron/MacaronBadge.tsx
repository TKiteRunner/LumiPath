import { cn } from "@/lib/utils";

const variants = {
  applied: "badge-applied",
  written_test: "badge-pending",
  first_interview: "badge-pending",
  second_interview: "badge-pending",
  third_interview: "badge-pending",
  fourth_interview: "badge-pending",
  hr_interview: "badge-pending",
  offer: "badge-offer",
  rejected: "badge-rejected",
  technical: "badge-technical",
  default: "bg-gray-100 text-gray-700",
};

interface MacaronBadgeProps {
  label: string;
  variant?: keyof typeof variants;
  className?: string;
}

export function MacaronBadge({
  label,
  variant = "default",
  className,
}: MacaronBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full",
        variants[variant] ?? variants.default,
        className
      )}
    >
      {label}
    </span>
  );
}
