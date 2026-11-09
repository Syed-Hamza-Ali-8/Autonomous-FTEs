// Run: npm run test:unit
import assert from "node:assert/strict";
import { test } from "node:test";

import { ACTION_TITLE, STATE_PILL, actionTitle } from "./action-meta.ts";

test("titles follow the spec's 'Refund · ORD-1042' form", () => {
  assert.equal(actionTitle("request_refund", "ORD-1042"), "Refund · ORD-1042");
  assert.equal(actionTitle("cancel_order", null), "Cancellation");
});

test("every action has a title and every state a labelled pill", () => {
  assert.equal(Object.keys(ACTION_TITLE).length, 6);
  assert.deepEqual(
    Object.values(STATE_PILL).map((p) => p.label),
    ["Completed", "Waiting for staff approval", "Not allowed"],
  );
});

test("only a completed action uses the success decision colour", () => {
  for (const [state, pill] of Object.entries(STATE_PILL)) {
    assert.equal(pill.decision === "completed", state === "completed", state);
  }
});
