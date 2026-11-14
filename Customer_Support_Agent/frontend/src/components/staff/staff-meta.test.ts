// Run: npm run test:unit
import assert from "node:assert/strict";
import { test } from "node:test";

import { APPROVAL_PILL, AUDIT_DECISION, CHECK_LABEL, approvalTitle, eventLabel, isSecurityIncident, nextAfter, sortQueue } from "./staff-meta.ts";

test("every approval state, check state and audit decision has a label", () => {
  assert.deepEqual(Object.keys(APPROVAL_PILL).sort(), ["approved", "expired", "failed_recheck", "pending", "rejected"]);
  for (const pill of Object.values(APPROVAL_PILL)) assert.ok(pill.label.length > 0);
  assert.deepEqual(Object.keys(CHECK_LABEL).sort(), ["fail", "needs_approval", "not_reached", "pass"]);
  assert.deepEqual(Object.keys(AUDIT_DECISION).sort(), ["ALLOW", "DENY", "NEEDS_APPROVAL"]);
});

test("a failed re-check and an expiry are not shown as rejections (J10)", () => {
  assert.notEqual(APPROVAL_PILL.failed_recheck.label, APPROVAL_PILL.rejected.label);
  assert.notEqual(APPROVAL_PILL.failed_recheck.decision, "not_allowed");
  assert.notEqual(APPROVAL_PILL.expired.decision, "not_allowed");
});

test("titles and event labels", () => {
  assert.equal(approvalTitle("request_refund", "ORD-1058"), "Refund · ORD-1058");
  assert.equal(eventLabel("action.cancel_order"), "Cancellation submitted");
  assert.equal(eventLabel("approval.failed_recheck"), "Decision: couldn't complete");
  assert.equal(eventLabel("something.else"), "something.else");
});

const items = [
  { reference: "ACT-1", queued_at: "2026-11-07T10:00:00Z", expires_at: "2026-11-09T10:00:00Z", amount: { amount_cents: 5100 } },
  { reference: "ACT-2", queued_at: "2026-11-07T09:00:00Z", expires_at: "2026-11-09T09:00:00Z", amount: { amount_cents: 20000 } },
  { reference: "ACT-3", queued_at: "2026-11-07T11:00:00Z", expires_at: "2026-11-09T11:00:00Z", amount: null },
];
const fraud = {
  reference: "ACT-4",
  queued_at: "2026-11-07T11:30:00Z",
  expires_at: "2026-11-09T11:30:00Z",
  amount: { amount_cents: 100 },
  risk_tags: [{ code: "fraud_signal" }],
};

test("the queue sorts by time left before expiry, or by amount (largest first)", () => {
  assert.deepEqual(sortQueue(items, "urgency").map((i) => i.reference), ["ACT-2", "ACT-1", "ACT-3"]);
  assert.deepEqual(sortQueue(items, "amount").map((i) => i.reference), ["ACT-2", "ACT-1", "ACT-3"]);
});

test("a suspected unauthorised order leads both sorts, however young and small it is", () => {
  assert.equal(sortQueue([...items, fraud], "urgency")[0].reference, "ACT-4");
  assert.equal(sortQueue([...items, fraud], "amount")[0].reference, "ACT-4");
  assert.equal(isSecurityIncident({ risk_tags: [{ code: "auto_max" }] }), false);
});

test("after a decision the next item is the one after it, else the one before", () => {
  assert.equal(nextAfter(items, "ACT-1"), "ACT-2");
  assert.equal(nextAfter(items, "ACT-3"), "ACT-2");
  assert.equal(nextAfter([items[0]], "ACT-1"), null);
});
