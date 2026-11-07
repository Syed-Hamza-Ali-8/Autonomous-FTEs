// Unit tests for the one money/date formatter (owner UI review item 3). Run: npm run test:unit
import assert from "node:assert/strict";
import { test } from "node:test";

import { formatDate, formatMoney, initials } from "./format.ts";

test("USD always shows cents", () => {
  assert.equal(formatMoney({ amount_cents: 3200, currency: "USD" }), "$32.00");
  assert.equal(formatMoney({ amount_cents: 5, currency: "USD" }), "$0.05");
  assert.equal(formatMoney({ amount_cents: 1234567, currency: "USD" }), "$12,345.67");
});

test("PKR drops .00 only when paisa is zero", () => {
  assert.equal(formatMoney({ amount_cents: 2649500, currency: "PKR" }), "Rs 26,495");
  assert.equal(formatMoney({ amount_cents: 2649550, currency: "PKR" }), "Rs 26,495.50");
  assert.equal(formatMoney({ amount_cents: 2649505, currency: "PKR" }), "Rs 26,495.05");
  assert.equal(formatMoney({ amount_cents: 0, currency: "PKR" }), "Rs 0");
  assert.equal(formatMoney({ amount_cents: 150000000, currency: "PKR" }), "Rs 1,500,000");
});

test("negative amounts keep the sign before the symbol", () => {
  assert.equal(formatMoney({ amount_cents: -2649500, currency: "PKR" }), "-Rs 26,495");
  assert.equal(formatMoney({ amount_cents: -3200, currency: "USD" }), "-$32.00");
});

test("dates are UTC day month year, matching the backend", () => {
  assert.equal(formatDate("2026-08-21T23:30:00Z"), "21 Aug 2026");
  assert.equal(formatDate("2026-08-22T02:00:00+05:00"), "21 Aug 2026");
  assert.equal(formatDate("2026-09-01T00:00:00Z"), "1 Sep 2026");
});

test("initials for product tiles", () => {
  assert.equal(initials("Electric Kettle 1.7L"), "EK");
  assert.equal(initials("Photo Editor Pro (licence)"), "PE");
  assert.equal(initials("Cookbook (e-book)"), "C");
});
