"use client";

import { ArrowLeft, Inbox as InboxIcon, ShieldAlert } from "lucide-react";
import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { toast } from "sonner";

import { DecisionPanel, type DialogKind } from "@/components/staff/decision-panel";
import { useStaffSearch } from "@/components/staff/staff-shell";
import { type QueueSort, approvalTitle, isSecurityIncident, nextAfter, sortQueue } from "@/components/staff/staff-meta";
import { TranscriptView } from "@/components/staff/transcript-view";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { ApiError, type ApprovalItem, type DecisionOut } from "@/lib/api";
import { formatMoney, formatStaffTimestamp, relativeTime, timeLeft } from "@/lib/format";
import { useApprovalDetail, useApprovalQueue, useDecide } from "@/lib/staff-queries";
import { cn } from "@/lib/utils";

const DONE: Record<DecisionOut["decision"], (ref: string) => string> = {
  approved: (r) => `Approved ${r}. It has been carried out.`,
  rejected: (r) => `Rejected ${r}. Nothing was changed.`,
  failed_recheck: (r) => `Couldn't complete ${r}: a rule now refuses it. Nothing was changed.`,
  expired: (r) => `${r} had expired. Nothing was changed.`,
};

const FAILED: Record<string, string> = {
  already_decided: "Someone has already decided this request.",
  amount_mismatch: "This request changed since you opened it. Check the amount and try again.",
  expired: "This request expired before it was decided. Nothing was changed.",
};

function matches(item: ApprovalItem, q: string): boolean {
  const s = q.trim().toLowerCase();
  if (!s) return true;
  return [item.reference, item.order_id ?? "", item.customer_id, item.customer_name].some((v) => v.toLowerCase().includes(s));
}

/** Support inbox (spec 13.4): queue, transcript with tool trace, decision panel. */
export default function InboxPage() {
  const queue = useApprovalQueue();
  const search = useStaffSearch();
  const [sort, setSort] = useState<QueueSort>("urgency");
  const [selected, setSelected] = useState<string | null>(null);
  const [dialog, setDialog] = useState<DialogKind>(null);
  const decide = useDecide();
  const items = useMemo(() => sortQueue((queue.data?.items ?? []).filter((i) => matches(i, search)), sort), [queue.data, search, sort]);
  // Wide screens show the first item when none is chosen; narrow ones start on the list (list -> detail).
  const wide = useSyncExternalStore(subscribeWide, isWide, () => false);
  const current = selected ?? (wide ? (items[0]?.reference ?? null) : null);
  const detail = useApprovalDetail(current);
  const now = queue.data ? new Date(queue.data.now) : new Date();

  async function run(d: Parameters<typeof decide.mutateAsync>[0]) {
    try {
      const out = await decide.mutateAsync(d);
      toast.success(DONE[out.decision](out.reference));
      setDialog(null);
      setSelected(nextAfter(items, d.reference));
    } catch (e) {
      const code = e instanceof ApiError ? e.code : "error";
      toast.error(FAILED[code] ?? "The decision couldn't be saved. Nothing was changed; try again.");
      setDialog(null);
    }
  }

  // J/K move through the queue, A approves, R rejects (spec 13.4). Never while typing or in a dialog.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const t = e.target as HTMLElement | null;
      if (dialog || e.metaKey || e.ctrlKey || e.altKey || t?.closest("input, textarea, select, [contenteditable], [role=dialog]")) return;
      const i = items.findIndex((x) => x.reference === current);
      const key = e.key.toLowerCase();
      if (key === "j" && items.length) setSelected(items[Math.min(i + 1, items.length - 1)].reference);
      else if (key === "k" && items.length) setSelected(items[Math.max(i - 1, 0)].reference);
      else if (key === "a" && detail.data?.approval.state === "pending") setDialog("approve");
      else if (key === "r" && detail.data?.approval.state === "pending") setDialog("reject");
      else return;
      e.preventDefault();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [items, current, dialog, detail.data]);

  const a = detail.data?.approval;
  return (
    <div className="grid min-h-0 flex-1 xl:grid-cols-[22rem_minmax(0,1fr)_26rem]">
      <section aria-label="Pending approvals" className={cn("min-h-0 flex-col border-r", current ? "hidden xl:flex" : "flex")}>
        <div className="flex items-center justify-between gap-2 border-b px-4 py-2.5">
          <h1 className="text-base font-semibold">Inbox</h1>
          {/* Security incidents lead either sort (staff-meta.ts); the active choice is filled, not just outlined. */}
          <ToggleGroup type="single" size="sm" variant="outline" value={sort} onValueChange={(v) => v && setSort(v as QueueSort)} aria-label="Sort by">
            {(
              [
                ["urgency", "Expires soonest"],
                ["amount", "Amount"],
              ] as const
            ).map(([value, label]) => (
              <ToggleGroupItem
                key={value}
                value={value}
                className="data-[state=on]:border-primary data-[state=on]:bg-primary data-[state=on]:text-primary-foreground data-[state=on]:hover:bg-primary/90"
              >
                {label}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </div>
        <QueueList state={queue} items={items} selected={current} onSelect={setSelected} now={now} filtered={search.trim() !== ""} />
      </section>

      <div className={cn("min-h-0 flex-col overflow-y-auto xl:contents", current ? "flex" : "hidden xl:contents")}>
        <div className="flex items-center gap-2 border-b px-4 py-2 xl:hidden">
          <Button variant="ghost" size="sm" onClick={() => setSelected(null)}>
            <ArrowLeft aria-hidden="true" /> Back to inbox
          </Button>
        </div>
        <section aria-label="Decision" className="order-1 border-b p-4 xl:order-3 xl:overflow-y-auto xl:border-b-0 xl:border-l">
          {current === null ? (
            <p className="text-sm text-muted-foreground">Select a request to decide on it.</p>
          ) : detail.isPending ? (
            <DetailSkeleton />
          ) : detail.error ? (
            <LoadError onRetry={() => void detail.refetch()} what="this request" />
          ) : detail.data ? (
            <DecisionPanel
              detail={detail.data}
              dialog={dialog}
              onDialog={setDialog}
              busy={decide.isPending}
              onApprove={() =>
                void run({ kind: "approve", reference: detail.data.approval.reference, amount_cents: detail.data.approval.amount?.amount_cents ?? null, currency: detail.data.approval.amount?.currency ?? null })
              }
              onReject={(note) => void run({ kind: "reject", reference: detail.data.approval.reference, note })}
            />
          ) : null}
        </section>
        <section aria-label="Transcript" className="order-2 min-w-0 p-4 xl:overflow-y-auto">
          <h2 className="mb-3 text-sm font-medium text-muted-foreground">
            {a ? `Conversation · ${a.customer_name} · ${approvalTitle(a.action, a.order_id)}` : "Conversation"}
          </h2>
          {detail.data?.transcript ? (
            <TranscriptView transcript={detail.data.transcript} />
          ) : detail.data ? (
            <p className="text-sm text-muted-foreground">This request has no conversation.</p>
          ) : current && detail.isPending ? (
            <Skeleton className="h-24 w-full" />
          ) : null}
        </section>
      </div>
    </div>
  );
}

function subscribeWide(onChange: () => void): () => void {
  const mq = window.matchMedia("(min-width: 1280px)");
  mq.addEventListener("change", onChange);
  return () => mq.removeEventListener("change", onChange);
}

function isWide(): boolean {
  return window.matchMedia("(min-width: 1280px)").matches;
}

function QueueList({
  state,
  items,
  selected,
  onSelect,
  now,
  filtered,
}: {
  state: ReturnType<typeof useApprovalQueue>;
  items: ApprovalItem[];
  selected: string | null;
  onSelect: (ref: string) => void;
  now: Date;
  filtered: boolean;
}) {
  if (state.isPending) {
    return (
      <div className="flex flex-col gap-2 p-4" aria-busy="true" aria-label="Loading the queue">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }
  if (state.error) return <LoadError onRetry={() => void state.refetch()} what="the queue" />;
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 px-6 py-12 text-center">
        <InboxIcon aria-hidden="true" className="size-6 text-muted-foreground" />
        <p className="text-sm font-medium">{filtered ? "No matching requests" : "Nothing waiting"}</p>
        <p className="text-sm text-muted-foreground">
          {filtered ? "Try another customer, order or reference." : "Requests that need a decision will appear here."}
        </p>
      </div>
    );
  }
  return (
    <ul className="min-h-0 flex-1 overflow-y-auto" aria-label="Queue">
      {items.map((item) => {
        const active = item.reference === selected;
        const incident = isSecurityIncident(item);
        return (
          <li key={item.reference} className={cn("border-b", incident && "border-l-4 border-l-foreground")}>
            <button
              type="button"
              onClick={() => onSelect(item.reference)}
              aria-current={active ? "true" : undefined}
              className={cn(
                "flex w-full flex-col gap-1 px-4 py-3 text-left outline-none hover:bg-muted/60 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:ring-inset",
                active && "bg-muted",
              )}
            >
              <span className="flex items-baseline justify-between gap-2">
                <span className="truncate text-sm font-medium">{item.customer_name}</span>
                {/* Time LEFT before expiry leads; the age stays as secondary text and on hover. */}
                <time dateTime={item.expires_at} title={`Expires ${formatStaffTimestamp(item.expires_at)}`} className="shrink-0 text-xs font-medium tabular-nums">
                  {timeLeft(item.expires_at, now)}
                </time>
              </span>
              <span className="flex items-baseline justify-between gap-2 text-sm">
                <span className="truncate text-muted-foreground">{approvalTitle(item.action, item.order_id)}</span>
                {item.amount && <span className="shrink-0 font-medium tabular-nums">{formatMoney(item.amount)}</span>}
              </span>
              {item.risk_tags.length > 0 && (
                <span className="flex flex-wrap gap-1">
                  {item.risk_tags.map((t) =>
                    t.code === "fraud_signal" ? (
                      // A security incident, not an approval threshold: inverted, with a shield (rose stays
                      // reserved for refusals, 13.2).
                      <span key={t.code} className="inline-flex items-center gap-1 rounded-md bg-foreground px-1.5 py-0.5 text-xs font-medium text-background">
                        <ShieldAlert aria-hidden="true" className="size-3.5" />
                        <span className="sr-only">Security: </span>
                        {t.label}
                      </span>
                    ) : (
                      <span key={t.code} className="rounded-md border border-warning-border bg-warning-muted px-1.5 py-0.5 text-xs text-warning-foreground">
                        {t.label}
                      </span>
                    ),
                  )}
                </span>
              )}
              <time dateTime={item.queued_at} title={`Queued ${formatStaffTimestamp(item.queued_at)}`} className="text-xs text-muted-foreground tabular-nums">
                Queued {relativeTime(item.queued_at, now)}
              </time>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

function DetailSkeleton() {
  return (
    <div className="flex flex-col gap-3" aria-busy="true" aria-label="Loading the request">
      <Skeleton className="h-6 w-2/3" />
      <Skeleton className="h-8 w-28" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-48 w-full" />
    </div>
  );
}

function LoadError({ onRetry, what }: { onRetry: () => void; what: string }) {
  return (
    <div role="alert" className="flex flex-col items-start gap-2 p-4">
      <p className="text-sm font-medium">Couldn&apos;t load {what}.</p>
      <p className="text-sm text-muted-foreground">Check your connection and try again.</p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        Try again
      </Button>
    </div>
  );
}
