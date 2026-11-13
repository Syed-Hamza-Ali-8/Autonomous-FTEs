"use client";

import { MessageSquareText, ScrollText } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { DecisionPill } from "@/components/decision-pill";
import { useStaffSearch } from "@/components/staff/staff-shell";
import { ACTION_FILTERS, AUDIT_DECISION, eventLabel } from "@/components/staff/staff-meta";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { AuditEntry } from "@/lib/api";
import { formatMoney, formatStaffTimestamp } from "@/lib/format";
import { type AuditFilters, PAGE_SIZE, useAudit } from "@/lib/staff-queries";

const ALL = "all";
const START: AuditFilters = { decision: null, action: null, customer: "", from: "", to: "", page: 1 };

/** Audit log (spec 13.4): filters, pagination, and a drawer with the full record. Times carry their zone (F2). */
export default function AuditPage() {
  const search = useStaffSearch();
  const [filters, setFilters] = useState<AuditFilters>(START);
  const [open, setOpen] = useState<AuditEntry | null>(null);
  // The top bar's search fills the customer filter when it looks like a customer id.
  const effective = { ...filters, customer: filters.customer || (/^cus-\d+$/i.test(search.trim()) ? search : "") };
  const audit = useAudit(effective);
  const set = (patch: Partial<AuditFilters>) => setFilters((f) => ({ ...f, ...patch, page: patch.page ?? 1 }));
  const total = audit.data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4">
      <h1 className="text-xl font-semibold">Audit log</h1>
      <form aria-label="Filters" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5" onSubmit={(e) => e.preventDefault()}>
        <div className="flex flex-col gap-1.5">
          {/* The POLICY verdict (incl. the approval re-check); the staff decision is the Outcome column. */}
          <Label htmlFor="f-decision">Policy</Label>
          <Select value={filters.decision ?? ALL} onValueChange={(v) => set({ decision: v === ALL ? null : (v as AuditFilters["decision"]) })}>
            <SelectTrigger id="f-decision" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Any policy verdict</SelectItem>
              {Object.entries(AUDIT_DECISION).map(([value, { label }]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="f-action">Action</Label>
          <Select value={filters.action ?? ALL} onValueChange={(v) => set({ action: v === ALL ? null : v })}>
            <SelectTrigger id="f-action" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Any action</SelectItem>
              {ACTION_FILTERS.map(({ value, label }) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="f-customer">Customer</Label>
          <Input id="f-customer" placeholder="CUS-025" value={filters.customer} onChange={(e) => set({ customer: e.target.value })} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="f-from">From (UTC)</Label>
          <Input id="f-from" type="date" value={filters.from} onChange={(e) => set({ from: e.target.value })} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="f-to">To (UTC, inclusive)</Label>
          <Input id="f-to" type="date" value={filters.to} onChange={(e) => set({ to: e.target.value })} />
        </div>
      </form>

      {audit.isPending ? (
        <div className="flex flex-col gap-2" aria-busy="true" aria-label="Loading the audit log">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : audit.error ? (
        <div role="alert" className="flex flex-col items-start gap-2">
          <p className="text-sm font-medium">Couldn&apos;t load the audit log.</p>
          <Button variant="outline" size="sm" onClick={() => void audit.refetch()}>
            Try again
          </Button>
        </div>
      ) : audit.data.items.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-12 text-center">
          <ScrollText aria-hidden="true" className="size-6 text-muted-foreground" />
          <p className="text-sm font-medium">No records match these filters</p>
          <Button variant="outline" size="sm" onClick={() => setFilters(START)}>
            Clear filters
          </Button>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-xl border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time (UTC)</TableHead>
                  <TableHead>Event</TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead>Target</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Policy</TableHead>
                  <TableHead>Outcome</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {audit.data.items.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell className="whitespace-nowrap tabular-nums">
                      <button
                        type="button"
                        className="rounded-md text-left underline-offset-4 outline-none hover:underline focus-visible:ring-3 focus-visible:ring-ring/50"
                        onClick={() => setOpen(e)}
                        aria-label={`Open record ${e.id}: ${eventLabel(e.event)}`}
                      >
                        {formatStaffTimestamp(e.at)}
                      </button>
                    </TableCell>
                    <TableCell>{eventLabel(e.event)}</TableCell>
                    <TableCell className="font-mono text-xs">
                      {e.actor_type} {e.actor_type === "customer" ? e.actor_id : ""}
                    </TableCell>
                    <TableCell className="font-mono text-xs">{e.target ?? "-"}</TableCell>
                    <TableCell className="text-right whitespace-nowrap tabular-nums">{e.amount ? formatMoney(e.amount) : "-"}</TableCell>
                    <TableCell>{e.decision && e.decision in AUDIT_DECISION ? <Pill decision={e.decision} /> : "-"}</TableCell>
                    <TableCell className="text-muted-foreground">{e.outcome ?? "-"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <nav aria-label="Pages" className="flex items-center justify-between gap-2 text-sm">
            <span className="text-muted-foreground tabular-nums">
              Page {filters.page} of {pages} · {total} records
            </span>
            <span className="flex gap-2">
              <Button variant="outline" size="sm" disabled={filters.page <= 1} onClick={() => set({ page: filters.page - 1 })}>
                Previous
              </Button>
              <Button variant="outline" size="sm" disabled={filters.page >= pages} onClick={() => set({ page: filters.page + 1 })}>
                Next
              </Button>
            </span>
          </nav>
        </>
      )}

      <Sheet open={open !== null} onOpenChange={(o) => !o && setOpen(null)}>
        <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
          {open && (
            <>
              <SheetHeader>
                <SheetTitle>{eventLabel(open.event)}</SheetTitle>
                <SheetDescription className="tabular-nums">
                  Record {open.id} · {formatStaffTimestamp(open.at)}
                </SheetDescription>
              </SheetHeader>
              <div className="flex flex-col gap-3 px-4 pb-6 text-sm">
                <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
                  <dt className="text-muted-foreground">Actor</dt>
                  <dd className="font-mono text-xs">
                    {open.actor_type} · {open.actor_id}
                  </dd>
                  <dt className="text-muted-foreground">Target</dt>
                  <dd className="font-mono text-xs">{open.target ?? "-"}</dd>
                  <dt className="text-muted-foreground">Amount</dt>
                  <dd className="tabular-nums">{open.amount ? formatMoney(open.amount) : "-"}</dd>
                  <dt className="text-muted-foreground">Policy</dt>
                  <dd>{open.decision && open.decision in AUDIT_DECISION ? <Pill decision={open.decision} /> : "-"}</dd>
                  <dt className="text-muted-foreground">Outcome</dt>
                  <dd>{open.outcome ?? "-"}</dd>
                  <dt className="text-muted-foreground">Reasons</dt>
                  <dd className="font-mono text-xs">{open.reasons.length ? open.reasons.join(", ") : "-"}</dd>
                </dl>
                <pre className="overflow-x-auto rounded-lg bg-muted/60 p-2 font-mono text-xs whitespace-pre-wrap break-all">{JSON.stringify(open.details, null, 2)}</pre>
                {open.conversation_id && (
                  <Link
                    href={`/console/conversations/${open.conversation_id}`}
                    className="inline-flex items-center gap-1.5 self-start rounded-lg text-primary underline-offset-4 outline-none hover:underline focus-visible:ring-3 focus-visible:ring-ring/50"
                  >
                    <MessageSquareText aria-hidden="true" className="size-4" /> Open conversation
                  </Link>
                )}
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}

function Pill({ decision }: { decision: string }) {
  const { decision: d, label } = AUDIT_DECISION[decision as keyof typeof AUDIT_DECISION];
  return <DecisionPill decision={d} label={label} />;
}
