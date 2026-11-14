"use client";

import { RotateCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { OrderRow } from "@/components/store/order-row";
import { FILTER_GROUPS, type FilterGroup } from "@/components/store/status-meta";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { OrderStatus } from "@/lib/api";
import { useOrders } from "@/lib/queries";
import { cn } from "@/lib/utils";

const GROUPS = Object.keys(FILTER_GROUPS) as FilterGroup[];

export default function OrdersPage() {
  const [filter, setFilter] = useState<FilterGroup>("all");
  const orders = useOrders(null); // one query; groups are filtered client-side
  const chips = useRef<Partial<Record<FilterGroup, HTMLButtonElement | null>>>({});
  const chipRow = useRef<HTMLDivElement>(null);
  const [moreRight, setMoreRight] = useState(false);
  const updateFade = useCallback(() => {
    const el = chipRow.current;
    if (el) setMoreRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 1);
  }, []);

  useEffect(() => {
    chips.current[filter]?.scrollIntoView({ block: "nearest", inline: "nearest" });
    updateFade();
  }, [filter, updateFade]);

  useEffect(() => {
    updateFade();
    window.addEventListener("resize", updateFade);
    return () => window.removeEventListener("resize", updateFade);
  }, [updateFade]);

  const statuses: readonly OrderStatus[] | null = FILTER_GROUPS[filter].statuses;
  const shown = orders.data?.filter((o) => statuses === null || statuses.includes(o.status));

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">My orders</h1>
        <p className="text-sm text-muted-foreground">Everything you&apos;ve ordered from Northwind Goods, newest first.</p>
      </div>

      {/* Mobile: one row that scrolls sideways (the page itself never does), with a soft fade on the
          right edge while more chips are hidden there. */}
      <div className="relative -mx-(--gutter) sm:mx-0">
      <div
        ref={chipRow}
        onScroll={updateFade}
        className="overflow-x-auto px-(--gutter) [scrollbar-width:none] sm:px-0"
      >
        <ToggleGroup
          type="single"
          variant="outline"
          size="sm"
          value={filter}
          onValueChange={(v) => v && setFilter(v as FilterGroup)}
          aria-label="Filter by status"
          className="flex w-max flex-nowrap justify-start gap-1.5"
          spacing={1}
        >
          {GROUPS.map((g) => (
            <ToggleGroupItem
              key={g}
              value={g}
              ref={(el) => {
                chips.current[g] = el;
              }}
              className="rounded-full px-3 whitespace-nowrap"
            >
              {FILTER_GROUPS[g].label}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>
      <div
        aria-hidden="true"
        className={cn(
          "pointer-events-none absolute inset-y-0 right-0 w-12 bg-linear-to-l from-background to-transparent transition-opacity sm:hidden",
          moreRight ? "opacity-100" : "opacity-0",
        )}
      />
      </div>

      {orders.isPending ? (
        <ul aria-label="Loading orders" className="flex flex-col gap-1">
          {Array.from({ length: 5 }, (_, i) => (
            <li key={i} className="flex items-center gap-4 px-3 py-3">
              <Skeleton className="hidden size-12 rounded-lg min-[400px]:block" />
              <div className="flex flex-1 flex-col gap-2">
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-3 w-1/3" />
              </div>
              <Skeleton className="h-4 w-16" />
            </li>
          ))}
        </ul>
      ) : orders.isError ? (
        <div role="alert" className="flex flex-col items-start gap-3 rounded-xl border p-6">
          <p className="font-medium">Your orders couldn&apos;t be loaded.</p>
          <p className="text-sm text-muted-foreground">This is usually a temporary connection problem.</p>
          <Button variant="outline" onClick={() => void orders.refetch()}>
            <RotateCw aria-hidden="true" /> Try again
          </Button>
        </div>
      ) : orders.data.length === 0 ? (
        <div className="flex flex-col items-start gap-2 rounded-xl border p-6">
          <p className="font-medium">No orders yet</p>
          <p className="text-sm text-muted-foreground">When you place an order, it will appear here.</p>
        </div>
      ) : !shown || shown.length === 0 ? (
        <div className="flex flex-col items-start gap-3 rounded-xl border p-6">
          <p className="font-medium">No {FILTER_GROUPS[filter].label.toLowerCase()} orders</p>
          <Button variant="outline" onClick={() => setFilter("all")}>
            Show all orders
          </Button>
        </div>
      ) : (
        <ul className="-mx-3 flex flex-col divide-y">
          {shown.map((o) => (
            <li key={o.id}>
              <OrderRow order={o} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
