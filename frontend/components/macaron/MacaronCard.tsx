import { cn } from "@/lib/utils";
import { HTMLAttributes, forwardRef } from "react";

interface MacaronCardProps extends HTMLAttributes<HTMLDivElement> {
  accent?: "pink" | "mint" | "lemon" | "lilac" | "sky" | "peach";
  noPadding?: boolean;
}

const accentMap = {
  pink: "border-l-4 border-l-macaron-pink",
  mint: "border-l-4 border-l-macaron-mint",
  lemon: "border-l-4 border-l-macaron-lemon",
  lilac: "border-l-4 border-l-macaron-lilac",
  sky: "border-l-4 border-l-macaron-sky",
  peach: "border-l-4 border-l-macaron-peach",
};

const MacaronCard = forwardRef<HTMLDivElement, MacaronCardProps>(
  ({ className, accent, noPadding, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "macaron-card",
        !noPadding && "p-4",
        accent && accentMap[accent],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);
MacaronCard.displayName = "MacaronCard";

export { MacaronCard };
