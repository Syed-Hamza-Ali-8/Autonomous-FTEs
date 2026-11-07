import { ORDER_STATUS } from "@/components/store/status-meta";
import type { OrderStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

export { ORDER_STATUS };

// Order status is a fact about the order, not a decision, so it uses neutral styling.
// Emerald / amber / rose / sky stay reserved for action decisions (Section 13.2).
export function StatusBadge({ status, className }: { status: OrderStatus; className?: string }) {
  const { label, icon: Icon } = ORDER_STATUS[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border px-2 py-0.5 text-xs font-medium whitespace-nowrap text-foreground",
        className,
      )}
    >
      <Icon aria-hidden="true" className="size-3.5 text-muted-foreground" />
      {label}
    </span>
  );
}
