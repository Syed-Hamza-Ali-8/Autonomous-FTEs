import Link from "next/link";

import { ProductTile } from "@/components/store/product-tile";
import { StatusBadge } from "@/components/store/status";
import type { OrderSummary } from "@/lib/api";
import { formatDate, formatMoney } from "@/lib/format";

/**
 * One order in My orders. Mobile: three lines (name; ID and date; price and status), no thumbnail
 * below 400px so the name isn't truncated. From 640px: one row with price and status on the right.
 */
export function OrderRow({ order }: { order: OrderSummary }) {
  const more = order.item_count > 1 ? ` and ${order.item_count - 1} more` : "";
  return (
    <Link
      href={`/orders/${order.id}`}
      className="flex items-center gap-4 rounded-xl px-3 py-3 outline-none hover:bg-muted/60 focus-visible:ring-3 focus-visible:ring-ring/50"
    >
      <ProductTile name={order.first_item_name} className="hidden min-[400px]:grid" />
      <div className="flex min-w-0 flex-1 flex-col gap-1.5 sm:flex-row sm:items-center sm:gap-4">
        <div className="min-w-0 flex-1">
          <p className="text-base font-medium sm:truncate">
            {order.first_item_name}
            <span className="font-normal text-muted-foreground">{more}</span>
          </p>
          <p className="text-sm text-muted-foreground">
            <span className="font-mono">{order.id}</span> · <span className="tabular-nums">{formatDate(order.placed_at)}</span>
          </p>
        </div>
        <div className="flex items-center justify-between gap-2 sm:flex-col sm:items-end sm:gap-1.5">
          <span className="text-base font-medium tabular-nums">{formatMoney(order.total)}</span>
          <StatusBadge status={order.status} />
        </div>
      </div>
    </Link>
  );
}
