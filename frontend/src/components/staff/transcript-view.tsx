"use client";

import { ChevronRight } from "lucide-react";

import { DecisionPill } from "@/components/decision-pill";
import { AUDIT_DECISION, eventLabel } from "@/components/staff/staff-meta";
import type { AuditEntry, Transcript } from "@/lib/api";
import { formatStaffTimestamp } from "@/lib/format";
import { cn } from "@/lib/utils";

type ToolCall = Transcript["tool_calls"][number];
type Turn = { id: string; messages: Transcript["messages"]; calls: ToolCall[]; actions: AuditEntry[] };

const ROLE: Record<Transcript["messages"][number]["role"], string> = {
  customer: "Customer",
  assistant: "Assistant",
  system: "System notice",
};

// Text a customer or the model wrote is a CLAIM, never console prose (DECISIONS L18): in adv01 a customer's invented
// approval reference reached staff as if it were fact. System notices are the store's own records.
const UNVERIFIED: Partial<Record<Transcript["messages"][number]["role"], string>> = {
  customer: "Unverified · written by the customer",
  assistant: "Unverified · written by the assistant",
};
const APPROVAL_REF = /\bAPR-\d+\b/g;

/** Each approval reference in `text`, with what app.approvals says about it, in words (not colour alone). */
function ReferenceChecks({ text, checks }: { text: string; checks: Map<string, boolean> }) {
  const refs = [...new Set(text.match(APPROVAL_REF) ?? [])];
  if (refs.length === 0) return null;
  return (
    <ul className="flex flex-wrap gap-x-3 gap-y-1 text-xs" aria-label="Approval references checked">
      {refs.map((r) => {
        const exists = checks.get(r);
        return (
          <li key={r} data-reference-check className="font-medium text-foreground">
            {r}: {exists === undefined ? "not checked" : exists ? "on record" : "not found"}
          </li>
        );
      })}
    </ul>
  );
}

/** A labelled, quoted block for text the console must not present as its own (L18). */
function Claim({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <blockquote data-claim="unverified" aria-label={label} className="flex flex-col gap-1 border-l-2 border-muted-foreground/50 pl-2">
      <span className="font-sans text-[11px] font-medium tracking-wide text-muted-foreground uppercase">{label}</span>
      {children}
    </blockquote>
  );
}

/** Messages grouped by turn, in order; each turn's tool calls and gateway decisions go with it. */
function turns(t: Transcript): Turn[] {
  const order: string[] = [];
  const byId = new Map<string, Turn>();
  const get = (id: string) => {
    let turn = byId.get(id);
    if (!turn) {
      turn = { id, messages: [], calls: [], actions: [] };
      byId.set(id, turn);
      order.push(id);
    }
    return turn;
  };
  for (const m of t.messages) get(m.turn_id).messages.push(m);
  for (const c of t.tool_calls) get(c.turn_id).calls.push(c);
  const decisions: AuditEntry[] = [];
  for (const a of t.actions) {
    if (a.turn_id) get(a.turn_id).actions.push(a);
    else decisions.push(a); // staff decisions belong to no turn
  }
  const out = order.map((id) => byId.get(id)!);
  if (decisions.length) out.push({ id: "decisions", messages: [], calls: [], actions: decisions });
  return out;
}

/** The full conversation (every role) with a collapsible tool trace per turn (spec 13.4). Read-only. */
export function TranscriptView({ transcript }: { transcript: Transcript }) {
  const all = turns(transcript);
  const checks = new Map((transcript.references ?? []).map((r) => [r.reference, r.exists]));
  if (all.length === 0) {
    return <p className="text-sm text-muted-foreground">No messages in this conversation yet.</p>;
  }
  return (
    <ol className="flex flex-col gap-4" aria-label="Conversation">
      {all.map((turn) => (
        <li key={turn.id} className="flex flex-col gap-2">
          {turn.messages.map((m, i) => (
            <div
              key={i}
              className={cn(
                "flex max-w-[44rem] flex-col gap-1 rounded-xl border px-3 py-2",
                m.role === "customer" && "bg-muted/60",
                m.role === "system" && "border-dashed",
              )}
            >
              <p className="flex flex-wrap items-baseline gap-x-2 text-xs text-muted-foreground">
                <span className="font-medium text-foreground">{ROLE[m.role]}</span>
                <time dateTime={m.at} className="tabular-nums">
                  {formatStaffTimestamp(m.at)}
                </time>
              </p>
              {UNVERIFIED[m.role] ? (
                <Claim label={UNVERIFIED[m.role]!}>
                  <p className="text-sm leading-relaxed break-words whitespace-pre-wrap">{m.content}</p>
                  <ReferenceChecks text={m.content} checks={checks} />
                </Claim>
              ) : (
                <p className="text-sm leading-relaxed break-words whitespace-pre-wrap">{m.content}</p>
              )}
            </div>
          ))}
          {(turn.calls.length > 0 || turn.actions.length > 0) && <TraceDetails turn={turn} checks={checks} />}
        </li>
      ))}
    </ol>
  );
}

function TraceDetails({ turn, checks }: { turn: Turn; checks: Map<string, boolean> }) {
  const label = turn.id === "decisions" ? "Staff decisions" : `Tool trace · ${turn.calls.length} call${turn.calls.length === 1 ? "" : "s"}`;
  return (
    <details className="group rounded-xl border bg-card">
      <summary className="flex cursor-pointer list-none items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-medium text-muted-foreground outline-none select-none focus-visible:ring-3 focus-visible:ring-ring/50 [&::-webkit-details-marker]:hidden">
        <ChevronRight aria-hidden="true" className="size-3.5 transition-transform group-open:rotate-90" />
        {label}
      </summary>
      <div className="flex flex-col gap-2 border-t px-3 py-2 font-mono text-xs">
        {turn.calls.map((c, i) => (
          <div key={`c${i}`} className="flex flex-col gap-0.5">
            <p className="flex flex-wrap gap-x-3">
              <span className="font-medium">{c.tool}</span>
              <span className="text-muted-foreground">{c.outcome}</span>
              <span className="text-muted-foreground tabular-nums">{c.latency_ms} ms</span>
            </p>
            {/* tool arguments are model-written: a ticket summary can carry a customer's claim as if it were fact */}
            <Claim label="Unverified · written by the assistant">
              <pre className="overflow-x-auto rounded-lg bg-muted/60 px-2 py-1 whitespace-pre-wrap break-all">{JSON.stringify(c.arguments)}</pre>
              <ReferenceChecks text={JSON.stringify(c.arguments)} checks={checks} />
            </Claim>
          </div>
        ))}
        {turn.actions.map((a) => (
          <div key={`a${a.id}`} className="flex flex-col gap-1">
            <p className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="font-sans font-medium">{eventLabel(a.event)}</span>
              {a.decision && a.decision in AUDIT_DECISION && (
                <DecisionPill decision={AUDIT_DECISION[a.decision as keyof typeof AUDIT_DECISION].decision} label={AUDIT_DECISION[a.decision as keyof typeof AUDIT_DECISION].label} />
              )}
              <span className="text-muted-foreground">{a.outcome}</span>
            </p>
            {a.reasons.length > 0 && <p className="text-muted-foreground">reasons: {a.reasons.join(", ")}</p>}
          </div>
        ))}
      </div>
    </details>
  );
}
