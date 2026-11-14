"use client";

import { CircleCheck, CircleX, Clock, ShieldCheck, ShieldAlert, type LucideIcon } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import type { Dashboard } from "@/lib/api";
import { formatStaffTimestamp } from "@/lib/format";
import { useDashboard } from "@/lib/staff-queries";
import { cn } from "@/lib/utils";

/**
 * Dashboard (spec 13.5; DECISIONS L20). The live row and charts come from the database; evaluation runs come from
 * the run files and sit in their own section below, never in the live row. "Resolution rate" is not shown: the spec
 * never defined it. A section with no data says so; a missing median or percentile is never shown as 0.
 */

type Series = { key: "completed" | "waiting_for_approval" | "refused"; label: string; icon: LucideIcon; color: string };
const SERIES: Series[] = [
  { key: "completed", label: "Completed", icon: CircleCheck, color: "var(--chart-completed)" },
  { key: "waiting_for_approval", label: "Waiting for approval", icon: Clock, color: "var(--chart-waiting)" },
  { key: "refused", label: "Refused", icon: CircleX, color: "var(--chart-refused)" },
];
const n = (v: number) => v.toLocaleString("en-US");

function duration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)} s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)} min`;
  const h = Math.floor(seconds / 3600);
  const m = Math.round((seconds % 3600) / 60);
  return m ? `${h} h ${m} min` : `${h} h`;
}

const ms = (v: number) => (v >= 1000 ? `${(v / 1000).toFixed(1)} s` : `${Math.round(v)} ms`);

function Tile({ label, children, className }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div role="group" aria-label={label} className={cn("flex flex-col gap-1.5 rounded-xl border bg-card p-4", className)}>
      <p className="text-sm text-muted-foreground">{label}</p>
      {children}
    </div>
  );
}

const Empty = ({ children }: { children: string }) => <p className="text-sm text-muted-foreground">{children}</p>;

function Legend() {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground" aria-label="Legend">
      {SERIES.map((s) => (
        <li key={s.key} className="flex items-center gap-1.5">
          <span aria-hidden="true" className="size-2.5 rounded-sm" style={{ background: s.color }} />
          <s.icon aria-hidden="true" className="size-3.5" />
          {s.label}
        </li>
      ))}
    </ul>
  );
}

/** Stacked bars by UTC day, 2px surface gaps between segments, a hover title per segment, and a table view. */
function ActionsByDay({ days }: { days: Dashboard["actions_by_day"] }) {
  const total = (d: Dashboard["actions_by_day"][number]) => d.completed + d.waiting_for_approval + d.refused;
  const max = Math.max(0, ...days.map(total));
  if (max === 0) return <Empty>No actions in the last 14 days</Empty>;
  return (
    <div className="flex flex-col gap-3">
      <Legend />
      <div className="flex h-40 items-end gap-1" role="img" aria-label="Actions by decision per day, last 14 days; the table below has the figures">
        {days.map((d) => (
          <div key={d.day} className="flex h-full min-w-0 flex-1 flex-col justify-end gap-[2px]">
            {SERIES.filter((s) => d[s.key] > 0)
              .reverse()
              .map((s, i, arr) => (
                <div
                  key={s.key}
                  title={`${d.day}: ${s.label} ${d[s.key]}`}
                  className={cn(i === 0 && "rounded-t-[4px]", i === arr.length - 1 && "rounded-b-[2px]")}
                  style={{ height: `${(d[s.key] / max) * 100}%`, background: s.color, minHeight: 2 }}
                />
              ))}
          </div>
        ))}
      </div>
      <div className="flex justify-between text-xs text-muted-foreground tabular-nums">
        <span>{days[0]?.day}</span>
        <span>{days[days.length - 1]?.day}</span>
      </div>
      <details className="text-sm">
        <summary className="cursor-pointer text-xs text-muted-foreground outline-none focus-visible:ring-3 focus-visible:ring-ring/50">Show as a table</summary>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-xs tabular-nums">
            <thead>
              <tr className="text-left text-muted-foreground">
                <th className="py-1 pr-3 font-medium">Day (UTC)</th>
                {SERIES.map((s) => (
                  <th key={s.key} className="py-1 pr-3 font-medium">{s.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {days.map((d) => (
                <tr key={d.day} className="border-t">
                  <td className="py-1 pr-3">{d.day}</td>
                  {SERIES.map((s) => (
                    <td key={s.key} className="py-1 pr-3">{d[s.key]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

const OUTCOME_LABEL: Record<string, string> = {
  approved: "Approved",
  rejected: "Rejected",
  expired: "Expired (not reviewed in time)",
  failed_recheck: "Couldn't complete (failed re-check)",
};

/** Horizontal bars, one neutral hue: the label carries identity, the value is printed. */
function ApprovalOutcomes({ outcomes }: { outcomes: Dashboard["approval_outcomes"] }) {
  const rows = Object.entries(outcomes);
  const max = Math.max(0, ...rows.map(([, v]) => v));
  if (max === 0) return <Empty>No approval decisions yet</Empty>;
  return (
    <ul className="flex flex-col gap-2">
      {rows.map(([k, v]) => (
        <li key={k} className="grid grid-cols-[minmax(0,12rem)_1fr_auto] items-center gap-3 text-sm">
          <span className="truncate text-muted-foreground" title={OUTCOME_LABEL[k] ?? k}>
            {OUTCOME_LABEL[k] ?? k}
          </span>
          <span className="h-3 rounded-r-[4px] bg-muted-foreground/40" style={{ width: `${(v / max) * 100}%`, minWidth: v ? 4 : 0 }} title={`${OUTCOME_LABEL[k] ?? k}: ${v}`} />
          <span className="tabular-nums">{v}</span>
        </li>
      ))}
    </ul>
  );
}

function LiveRow({ d }: { d: Dashboard }) {
  const a = d.actions_last_24h;
  const anyAction = a.completed + a.waiting_for_approval + a.refused > 0;
  const tokenShare = d.tokens.budget ? Math.round((d.tokens.used_24h / d.tokens.budget) * 100) : null;
  const unsafe = d.unsafe_live;
  return (
    <section aria-label="Live metrics" className="flex flex-col gap-3">
      <h2 className="text-sm font-medium text-muted-foreground">Live, from the database</h2>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <Tile label="Actions, last 24 hours">
          {anyAction ? (
            <ul className="flex flex-col gap-1 text-sm">
              {SERIES.map((s) => (
                <li key={s.key} className="flex items-center gap-2">
                  <s.icon aria-hidden="true" className="size-4" style={{ color: s.color }} />
                  <span className="flex-1">{s.label}</span>
                  <span className="font-semibold tabular-nums">{a[s.key]}</span>
                </li>
              ))}
            </ul>
          ) : (
            <Empty>No actions in the last 24 hours</Empty>
          )}
        </Tile>
        <Tile label="Approvals pending">
          <p className="text-3xl font-semibold tabular-nums">{n(d.approvals_pending)}</p>
        </Tile>
        <Tile label="Median time to approval">
          {d.time_to_approval.median_seconds === null ? (
            <Empty>No staff decisions yet</Empty>
          ) : (
            <>
              <p className="text-3xl font-semibold tabular-nums">{duration(d.time_to_approval.median_seconds)}</p>
              <p className="text-xs text-muted-foreground">across {n(d.time_to_approval.decisions)} staff decision{d.time_to_approval.decisions === 1 ? "" : "s"}</p>
            </>
          )}
        </Tile>
        <Tile label="Tokens, last 24 hours">
          <p className="text-3xl font-semibold tabular-nums">{n(d.tokens.used_24h)}</p>
          <p className="text-xs text-muted-foreground">
            of {n(d.tokens.budget)} ({tokenShare}%) · <span className="font-mono">{d.tokens.model}</span>
          </p>
        </Tile>
        <Tile label="Unsafe actions, live check" className={cn(unsafe.count > 0 && "border-danger-border")}>
          <p className="flex items-center gap-2 text-3xl font-semibold tabular-nums">
            {unsafe.count === 0 ? <ShieldCheck aria-hidden="true" className="size-6 text-success" /> : <ShieldAlert aria-hidden="true" className="size-6 text-danger" />}
            {unsafe.count}
            <span className="text-sm font-normal text-muted-foreground">{unsafe.count === 0 ? "none found (should read 0)" : "found (should read 0)"}</span>
          </p>
          {unsafe.findings.length > 0 && (
            <ul className="list-disc pl-4 text-xs">
              {unsafe.findings.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          )}
          <p className="text-xs text-muted-foreground">{unsafe.definition}</p>
        </Tile>
      </div>
    </section>
  );
}

function Charts({ d }: { d: Dashboard }) {
  const l = d.latency;
  return (
    <section aria-label="Live charts" className="grid gap-3 lg:grid-cols-3">
      <div className="flex flex-col gap-3 rounded-xl border bg-card p-4 lg:col-span-2">
        <h2 className="text-sm font-medium">Actions by decision, last 14 days</h2>
        <ActionsByDay days={d.actions_by_day} />
      </div>
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-3 rounded-xl border bg-card p-4">
          <h2 className="text-sm font-medium">Approval outcomes</h2>
          <ApprovalOutcomes outcomes={d.approval_outcomes} />
        </div>
        <Tile label="Reply latency, last 7 days">
          {l.p50_ms === null || l.p95_ms === null ? (
            <Empty>No replies in the last 7 days</Empty>
          ) : (
            <>
              <dl className="grid grid-cols-2 gap-2">
                <div>
                  <dt className="text-xs text-muted-foreground">p50</dt>
                  <dd className="text-2xl font-semibold tabular-nums">{ms(l.p50_ms)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">p95</dt>
                  <dd className="text-2xl font-semibold tabular-nums">{ms(l.p95_ms)}</dd>
                </div>
              </dl>
              <p className="text-xs text-muted-foreground">
                across {n(l.turns)} real-model repl{l.turns === 1 ? "y" : "ies"} (replays excluded). Evaluation runs are paced to the free-tier rate limit, so
                their turns include waiting time.
              </p>
            </>
          )}
        </Tile>
      </div>
    </section>
  );
}

function EvalRuns({ d }: { d: Dashboard }) {
  return (
    <section aria-label="Evaluation runs" className="flex flex-col gap-3 border-t pt-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-base font-semibold">Evaluation runs</h2>
        <p className="text-sm text-muted-foreground">From the eval run files in the repository: recorded test runs, not live data. Replays (re-scorings) are left out.</p>
      </div>
      {d.eval_runs.length === 0 ? (
        <Empty>No evaluation runs</Empty>
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Run</th>
                <th className="px-3 py-2 font-medium">Date</th>
                <th className="px-3 py-2 font-medium">Prompt</th>
                <th className="px-3 py-2 font-medium">Task success</th>
                <th className="px-3 py-2 font-medium">Unsafe (pre-registered)</th>
                <th className="px-3 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {d.eval_runs.map((r, i) => (
                <tr key={r.run_id} className="border-t">
                  <td className="px-3 py-2 font-mono text-xs whitespace-nowrap">
                    {r.run_id}
                    {i === 0 && <span className="ml-2 rounded-md border px-1.5 py-0.5 font-sans text-[11px] text-muted-foreground">Latest</span>}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap tabular-nums">{r.date}</td>
                  <td className="px-3 py-2 font-mono text-xs">{r.prompt_version ?? "—"}</td>
                  <td className="px-3 py-2 tabular-nums">
                    {r.task_success} of {r.scenarios}
                  </td>
                  <td className="px-3 py-2 tabular-nums">{r.unsafe_total ?? "not scored"}</td>
                  <td className="px-3 py-2">{r.complete ? "Complete" : "Stopped"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-xs text-muted-foreground">Unsafe (pre-registered): {d.eval_unsafe_definition}</p>
    </section>
  );
}

export default function DashboardPage() {
  const q = useDashboard();
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-xl font-semibold">Dashboard</h1>
        {q.data && <p className="text-xs text-muted-foreground">As of {formatStaffTimestamp(q.data.now)}</p>}
      </div>
      {q.isPending ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5" aria-label="Loading">
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      ) : q.isError ? (
        <p role="alert" className="rounded-xl border border-danger-border bg-danger-muted p-4 text-sm text-danger-foreground">
          The dashboard couldn&apos;t load. Try again in a moment.
        </p>
      ) : (
        <>
          <LiveRow d={q.data} />
          <Charts d={q.data} />
          <EvalRuns d={q.data} />
        </>
      )}
    </div>
  );
}
