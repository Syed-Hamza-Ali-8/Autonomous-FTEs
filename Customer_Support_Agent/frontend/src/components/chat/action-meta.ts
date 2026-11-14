// What an ActionCard says for each action and state (spec 13.3). Kept apart from the component so the
// labels are unit-tested (npm run test:unit).

export type ActionKind =
  | "request_refund"
  | "issue_store_credit"
  | "cancel_order"
  | "update_shipping_address"
  | "create_ticket"
  | "escalate_to_human";
export type ActionState = "completed" | "waiting_for_approval" | "not_allowed" | "not_completed" | "closed";

export const ACTION_TITLE: Record<ActionKind, string> = {
  request_refund: "Refund",
  issue_store_credit: "Store credit",
  cancel_order: "Cancellation",
  update_shipping_address: "Address change",
  create_ticket: "Support ticket",
  escalate_to_human: "Handover to our team",
};

// The pill uses the reserved decision colours (13.2) and always carries a label and an icon.
// "closed": a request that waited too long for review (DECISIONS J8). "not_completed": approved, but the
// order had changed by then (J10). Neither is a refusal, so both use the neutral info colour, never danger.
export const STATE_PILL: Record<ActionState, { decision: "completed" | "waiting" | "not_allowed" | "info"; label: string }> = {
  completed: { decision: "completed", label: "Completed" },
  waiting_for_approval: { decision: "waiting", label: "Waiting for staff approval" },
  not_allowed: { decision: "not_allowed", label: "Not allowed" },
  not_completed: { decision: "info", label: "Couldn't complete" },
  closed: { decision: "info", label: "Closed" },
};

/**
 * The pill for a card. A request refused at once by policy is "Not allowed"; one that staff reviewed and
 * turned down (it has an action record) is "Not approved" (J10).
 */
export function statePill(state: ActionState, reviewedByStaff: boolean) {
  return state === "not_allowed" && reviewedByStaff ? { ...STATE_PILL[state], label: "Not approved" } : STATE_PILL[state];
}

/** "Refund · ORD-1042", or just "Refund" when no order is named (e.g. it wasn't found). */
export function actionTitle(action: ActionKind, orderId: string | null | undefined): string {
  return orderId ? `${ACTION_TITLE[action]} · ${orderId}` : ACTION_TITLE[action];
}
