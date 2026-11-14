// Run: npm run test:unit
import assert from "node:assert/strict";
import { test } from "node:test";

import { suggestionsFor } from "./suggestions.ts";

const ALL = ["pending", "paid", "packed", "shipped", "delivered", "cancelled", "refunded", "partially_refunded"] as const;
const LEFT_WAREHOUSE = new Set(["shipped", "delivered", "refunded", "partially_refunded", "cancelled"]);

test("address change is never offered once an order has left the warehouse", () => {
  for (const status of ALL) {
    const chips = suggestionsFor({ id: "ORD-1106", status, item_count: 2 });
    const offersAddress = chips.some((c) => /address/i.test(c));
    if (LEFT_WAREHOUSE.has(status)) assert.equal(offersAddress, false, status);
  }
});

test("delivered order gets the owner's three chips", () => {
  assert.deepEqual(suggestionsFor({ id: "ORD-1106", status: "delivered", item_count: 1 }), [
    "Where is ORD-1106?",
    "Refund an item",
    "Something's wrong with it",
  ]);
});

test("every status has 1-3 chips; no order gives the general ones", () => {
  for (const status of ALL) {
    const n = suggestionsFor({ id: "ORD-1", status, item_count: 1 }).length;
    assert.ok(n >= 1 && n <= 3, status);
  }
  assert.equal(suggestionsFor(null).length, 3);
});

test("'another item' is only offered when the order has more than one item", () => {
  const one = suggestionsFor({ id: "ORD-1106", status: "partially_refunded", item_count: 1 });
  const two = suggestionsFor({ id: "ORD-1106", status: "partially_refunded", item_count: 2 });
  assert.equal(one.some((c) => /another item/.test(c)), false);
  assert.equal(two.some((c) => /another item/.test(c)), true);
});
