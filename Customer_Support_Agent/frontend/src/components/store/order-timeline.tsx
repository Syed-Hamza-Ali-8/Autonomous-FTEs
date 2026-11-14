import { CircleX } from "lucide-react";

import type { OrderDetail } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

const REACHED: Record<OrderDetail["status"], number> = {
  pending: 0,
  paid: 1,
  packed: 2,
  shipped: 3,
  delivered: 4,
  refunded: 4,
  partially_refunded: 4,
  cancelled: -1,
};

function steps(order: OrderDetail): { label: string; date: string | null }[] {
  const d = (iso: string | null | undefined) => (iso ? formatDate(iso) : null);
  return [
    { label: "Placed", date: d(order.placed_at) },
    { label: "Paid", date: d(order.paid_at) },
    { label: "Packed", date: d(order.packed_at) },
    { label: "Shipped", date: d(order.shipment?.shipped_at) },
    { label: "Delivered", date: d(order.delivered_at) },
  ];
}

/**
 * The order's route. Reached stops are filled in the accent and the current one is ringed.
 * Horizontal from 640px; vertical below it (dots on the left, step and date beside each).
 * A cancelled order shows a plain notice instead of a misleading partial route.
 */
export function OrderTimeline({ order }: { order: OrderDetail }) {
  const reached = REACHED[order.status];
  if (reached < 0) {
    return (
      <p className="flex items-center gap-2 text-sm">
        <CircleX aria-hidden="true" className="size-4 text-muted-foreground" />
        This order was cancelled. Nothing was shipped.
      </p>
    );
  }
  return (
    <ol aria-label="Order progress" className="flex flex-col sm:grid sm:grid-cols-5">
      {steps(order).map(({ label, date }, i) => {
        const done = i <= reached;
        const current = i === reached;
        return (
          <li
            key={label}
            aria-current={current ? "step" : undefined}
            className="relative flex items-start gap-3 pb-5 last:pb-0 sm:flex-col sm:items-center sm:gap-2 sm:pb-0 sm:text-center"
          >
            {/* mobile: line DOWN from this dot to the next (row height = distance between dots) */}
            {i < 4 && (
              <span
                aria-hidden="true"
                className={cn("absolute top-[10px] left-[7px] h-full w-0.5 sm:hidden", i + 1 <= reached ? "bg-primary" : "bg-border")}
              />
            )}
            {/* sm and up: horizontal line from the previous stop's centre to this one's */}
            {i > 0 && (
              <span
                aria-hidden="true"
                className={cn("absolute top-[7px] right-1/2 hidden h-0.5 w-full sm:block", done ? "bg-primary" : "bg-border")}
              />
            )}
            <span
              aria-hidden="true"
              className={cn(
                "relative z-10 mt-0.5 size-4 shrink-0 rounded-full border-2 sm:mt-0",
                done ? "border-primary bg-primary" : "border-input bg-background",
                current && "ring-4 ring-primary/20",
              )}
            />
            <span className="flex flex-col gap-0.5 sm:items-center">
              <span className={cn("text-sm sm:text-xs", current ? "font-medium" : done ? "" : "text-muted-foreground")}>
                {label}
                <span className="sr-only">{done ? (current ? ", current step" : ", done") : ", not yet"}</span>
              </span>
              <span className="min-h-4 text-xs text-muted-foreground tabular-nums">{done ? (date ?? "") : ""}</span>
            </span>
          </li>
        );
      })}
    </ol>
  );
}
