import { CircleCheck, CircleX, Clock, Info, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

// Section 13.2: the reserved decision colours, always colour + icon + label, used the same way
// everywhere (refund rows now; ActionCards from Phase 3).
export type Decision = "completed" | "waiting" | "not_allowed" | "info";

const STYLE: Record<Decision, { icon: LucideIcon; className: string }> = {
  completed: { icon: CircleCheck, className: "border-success-border bg-success-muted text-success-foreground [&_svg]:text-success" },
  waiting: { icon: Clock, className: "border-warning-border bg-warning-muted text-warning-foreground [&_svg]:text-warning" },
  not_allowed: { icon: CircleX, className: "border-danger-border bg-danger-muted text-danger-foreground [&_svg]:text-danger" },
  info: { icon: Info, className: "border-info-border bg-info-muted text-info-foreground [&_svg]:text-info" },
};

export function DecisionPill({ decision, label, className }: { decision: Decision; label: string; className?: string }) {
  const { icon: Icon, className: tone } = STYLE[decision];
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-lg border px-2 py-0.5 text-xs font-medium whitespace-nowrap", tone, className)}>
      <Icon aria-hidden="true" className="size-3.5" />
      {label}
    </span>
  );
}
