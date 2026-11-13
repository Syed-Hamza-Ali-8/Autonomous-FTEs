// Staff console vocabulary (spec 13.4). Kept apart from the components so it is unit-tested
// (npm run test:unit). Staff surfaces may show reasons, codes and limits (tier C, DECISIONS I15).

import { ACTION_TITLE, type ActionKind } from "../chat/action-meta.ts";

export type Decision = "completed" | "waiting" | "not_allowed" | "info";
export type ApprovalState = "pending" | "expired" | "approved" | "rejected" | "failed_recheck";
export type CheckState = "pass" | "fail" | "not_reached" | "needs_approval";

/** Every approval state has a labelled pill; status is never shown by colour alone (13.6). */
export const APPROVAL_PILL: Record<ApprovalState, { decision: Decision; label: string }> = {
  pending: { decision: "waiting", label: "Waiting for a decision" },
  approved: { decision: "completed", label: "Approved" },
  rejected: { decision: "not_allowed", label: "Rejected" },
  failed_recheck: { decision: "info", label: "Couldn't complete" },
  expired: { decision: "info", label: "Expired, not reviewed in time" },
};

export const CHECK_LABEL: Record<CheckState, string> = {
  pass: "Passes",
  fail: "Refuses",
  not_reached: "Not reached",
  needs_approval: "Needs approval",
};

export const AUDIT_DECISION: Record<"ALLOW" | "NEEDS_APPROVAL" | "DENY", { decision: Decision; label: string }> = {
  ALLOW: { decision: "completed", label: "Allowed" },
  NEEDS_APPROVAL: { decision: "waiting", label: "Needs approval" },
  DENY: { decision: "not_allowed", label: "Denied" },
};

export const ACTION_FILTERS: { value: ActionKind; label: string }[] = (Object.keys(ACTION_TITLE) as ActionKind[]).map(
  (value) => ({ value, label: ACTION_TITLE[value] }),
);

/** "Refund · ORD-1058" for the queue and panel headers. */
export function approvalTitle(action: ActionKind, orderId: string | null | undefined): string {
  return orderId ? `${ACTION_TITLE[action]} · ${orderId}` : ACTION_TITLE[action];
}

/** "action.request_refund" -> "Refund submitted"; "approval.failed_recheck" -> "Decision: couldn't complete". */
export function eventLabel(event: string): string {
  const [kind, rest = ""] = event.split(".", 2);
  if (kind === "action" && rest in ACTION_TITLE) return `${ACTION_TITLE[rest as ActionKind]} submitted`;
  if (kind === "approval" && rest in APPROVAL_PILL) return `Decision: ${APPROVAL_PILL[rest as ApprovalState].label.toLowerCase()}`;
  if (event === "tool_call_rejected") return "Tool call rejected (schema)";
  return event;
}

type Sortable = {
  queued_at: string;
  expires_at: string;
  amount?: { amount_cents: number } | null;
  risk_tags?: readonly { code: string }[];
};
export type QueueSort = "urgency" | "amount";

/** A suspected unauthorised order is a security incident, not just a large amount: it leads every sort. */
export function isSecurityIncident(item: { risk_tags?: readonly { code: string }[] }): boolean {
  return (item.risk_tags ?? []).some((t) => t.code === "fraud_signal");
}

/**
 * Queue order. Security incidents first, always; then by urgency (least time left before expiry) or by amount
 * (largest first, ties by urgency).
 */
export function sortQueue<T extends Sortable>(items: readonly T[], by: QueueSort): T[] {
  const urgency = (a: T, b: T) => a.expires_at.localeCompare(b.expires_at) || a.queued_at.localeCompare(b.queued_at);
  const amount = (a: T, b: T) => (b.amount?.amount_cents ?? -1) - (a.amount?.amount_cents ?? -1);
  const incident = (a: T, b: T) => Number(isSecurityIncident(b)) - Number(isSecurityIncident(a));
  return [...items].sort((a, b) => incident(a, b) || (by === "amount" ? amount(a, b) : 0) || urgency(a, b));
}

/** The next item to show after one is decided: the one after it, else the one before, else none. */
export function nextAfter<T extends { reference: string }>(items: readonly T[], decided: string): string | null {
  const i = items.findIndex((x) => x.reference === decided);
  const rest = items.filter((x) => x.reference !== decided);
  if (rest.length === 0) return null;
  return (rest[Math.min(Math.max(i, 0), rest.length - 1)] ?? rest[0]).reference;
}
