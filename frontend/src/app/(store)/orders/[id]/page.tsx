"use client";

import { ChevronLeft, MessageCircle, RotateCw } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { useChatControls } from "@/components/chat/chat-provider";
import { OrderTimeline } from "@/components/store/order-timeline";
import { ProductTile } from "@/components/store/product-tile";
import { StatusBadge } from "@/components/store/status";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { DecisionPill, type Decision } from "@/components/decision-pill";
import { ApiError, type OrderDetail, type OrderSummary } from "@/lib/api";
import { formatDate, formatMoney } from "@/lib/format";
import { useOrder } from "@/lib/queries";
import { cn } from "@/lib/utils";

export default function OrderPage() {
  const { id } = useParams<{ id: string }>();
  const order = useOrder(id);

  return (
    <div className="flex flex-col gap-6">
      <Link
        href="/orders"
        className="-ml-1 flex w-fit items-center gap-1 rounded-lg text-sm text-muted-foreground outline-none hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50"
      >
        <ChevronLeft aria-hidden="true" className="size-4" /> My orders
      </Link>
      {order.isPending ? (
        <OrderSkeleton />
      ) : order.isError ? (
        order.error instanceof ApiError && order.error.status === 404 ? (
          <div className="flex flex-col items-start gap-2 rounded-xl border p-6">
            <h1 className="text-xl font-semibold">Order not found</h1>
            <p className="text-sm text-muted-foreground">
              There&apos;s no order <span className="font-mono">{id}</span> on your account. Check the order number, or
              find it in My orders.
            </p>
          </div>
        ) : (
          <div role="alert" className="flex flex-col items-start gap-3 rounded-xl border p-6">
            <p className="font-medium">This order couldn&apos;t be loaded.</p>
            <Button variant="outline" onClick={() => void order.refetch()}>
              <RotateCw aria-hidden="true" /> Try again
            </Button>
          </div>
        )
      ) : (
        <Order order={order.data} />
      )}
    </div>
  );
}

function Order({ order }: { order: OrderDetail }) {
  const { openChat } = useChatControls();
  const ccy = order.total.currency;
  const net = { amount_cents: order.captured.amount_cents - order.refunded.amount_cents, currency: ccy };
  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            Order <span className="font-mono">{order.id}</span>
          </h1>
          <p className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            Placed {formatDate(order.placed_at)}
            <StatusBadge status={order.status} />
          </p>
        </div>
        <Button onClick={() => openChat(toSummary(order))}>
          <MessageCircle aria-hidden="true" /> Get help with this order
        </Button>
      </div>

      <section aria-label="Progress" className="rounded-xl border px-4 pt-5 pb-3">
        <OrderTimeline order={order} />
      </section>

      {/* One grid: phones read Items, Refunds, Payment, Delivery (DOM order); from lg,
          Items, Refunds and Delivery stack on the left and Payment sits alone on the right. */}
      <div className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:items-start">
        <Section className="lg:col-start-1 lg:row-start-1" title="Items">
          <ul className="flex flex-col divide-y">
            {order.items.map((item) => (
              <li key={item.product_id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
                <ProductTile name={item.name} size="sm" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{item.name}</p>
                  <p className="text-xs text-muted-foreground tabular-nums">
                    {item.quantity} × {formatMoney(item.unit_price)}
                    {item.final_sale && ", final sale (not refundable)"}
                    {item.digital && ", digital"}
                  </p>
                </div>
                <span className="text-sm tabular-nums">{formatMoney(item.line_total)}</span>
              </li>
            ))}
          </ul>
        </Section>

        <Section className="lg:col-start-1 lg:row-start-2" title="Refunds">
          {order.refunds.length === 0 ? (
            <p className="text-sm text-muted-foreground">No refunds on this order.</p>
          ) : (
            <ul className="flex flex-col divide-y">
              {order.refunds.map((r) => (
                <li key={r.id} className="flex items-start justify-between gap-3 py-2.5 first:pt-0 last:pb-0">
                  <div className="flex flex-col gap-1">
                    <p className="text-sm">{r.reason ?? "Refund"}</p>
                    <p className="text-xs text-muted-foreground">
                      <span className="font-mono">{r.id}</span>, {formatDate(r.created_at)}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className="text-sm tabular-nums">{formatMoney(r.amount)}</span>
                    <DecisionPill {...REFUND_STATUS[r.status]} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section className="lg:col-start-2 lg:row-span-3 lg:row-start-1" title="Payment">
          <dl className="grid grid-cols-[1fr_auto] gap-y-1.5 text-sm">
            <dt className="text-muted-foreground">Order total</dt>
            <dd className="text-right tabular-nums">{formatMoney(order.total)}</dd>
            <dt className="text-muted-foreground">Paid</dt>
            <dd className="text-right tabular-nums">{formatMoney(order.captured)}</dd>
            <dt className="text-muted-foreground">Refunded</dt>
            <dd className="text-right tabular-nums">{formatMoney(order.refunded)}</dd>
            <dt className="border-t pt-1.5 font-medium">Net paid</dt>
            <dd className="border-t pt-1.5 text-right font-medium tabular-nums">{formatMoney(net)}</dd>
          </dl>
        </Section>

        <Section className="lg:col-start-1 lg:row-start-3" title="Delivery">
          <address className="text-sm not-italic">
            {order.shipping_address.name}
            <br />
            {order.shipping_address.line1}
            <br />
            {order.shipping_address.city} {order.shipping_address.postal_code}, {order.shipping_address.country}
          </address>
          {order.shipment ? (
            <div className="mt-4 flex flex-col gap-2 border-t pt-4 text-sm">
              <p>
                {order.shipment.carrier}, tracking <span className="font-mono">{order.shipment.tracking_number}</span>
              </p>
              <ol className="flex flex-col gap-1 text-xs text-muted-foreground">
                {order.shipment.events.map((e) => (
                  <li key={`${e.at}-${e.description}`} className="tabular-nums">
                    {formatDate(e.at)}: {e.description}
                  </li>
                ))}
              </ol>
            </div>
          ) : (
            <p className="mt-4 border-t pt-4 text-sm text-muted-foreground">
              {order.status === "cancelled" ? "This order won't be shipped." : "Not handed to a carrier yet."}
            </p>
          )}
        </Section>
      </div>
    </>
  );
}

const REFUND_STATUS: Record<OrderDetail["refunds"][number]["status"], { decision: Decision; label: string }> = {
  succeeded: { decision: "completed", label: "Completed" },
  pending_approval: { decision: "waiting", label: "Waiting for staff approval" },
  rejected: { decision: "not_allowed", label: "Not approved" },
};

function toSummary(order: OrderDetail): OrderSummary {
  return {
    id: order.id,
    status: order.status,
    total: order.total,
    placed_at: order.placed_at,
    delivered_at: order.delivered_at,
    item_count: order.items.length,
    first_item_name: order.items[0]?.name ?? "",
  };
}

function Section({ title, children, className }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <section aria-label={title} className={cn("rounded-xl border p-4", className)}>
      <h2 className="mb-3 text-base font-medium">{title}</h2>
      {children}
    </section>
  );
}

function OrderSkeleton() {
  return (
    <div className="flex flex-col gap-6" aria-label="Loading order" aria-busy="true">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-24 w-full rounded-xl" />
      <div className="grid gap-6 lg:grid-cols-[3fr_2fr]">
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
    </div>
  );
}
