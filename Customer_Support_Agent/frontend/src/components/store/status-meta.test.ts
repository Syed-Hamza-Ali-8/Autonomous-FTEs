// Run: npm run test:unit
import assert from "node:assert/strict";
import { test } from "node:test";

import * as icons from "lucide-react";

import { FILTER_GROUPS, ORDER_STATUS } from "./status-meta.ts";

const CHECK_ICONS = Object.entries(icons)
  .filter(([name]) => /check/i.test(name) && !/checkbox|checkout/i.test(name))
  .map(([, icon]) => icon);

test("no non-success status uses a check-style icon", () => {
  for (const [status, meta] of Object.entries(ORDER_STATUS)) {
    const isCheck = CHECK_ICONS.includes(meta.icon);
    assert.equal(isCheck, meta.success, `${status}: check icon=${isCheck}, success=${meta.success}`);
  }
});

test("cancelled uses the x-circle icon", () => {
  assert.equal(ORDER_STATUS.cancelled.icon, icons.CircleX);
});

test("filter groups cover every status exactly once", () => {
  const grouped = Object.values(FILTER_GROUPS).flatMap((g) => g.statuses ?? []);
  assert.deepEqual([...grouped].sort(), Object.keys(ORDER_STATUS).sort());
});
