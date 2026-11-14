import { expect, test, type Page } from "@playwright/test";

import { staffLogin } from "./helpers";

/**
 * The dashboard (spec 13.5; DECISIONS L20; Phase 7 pre-registration item 3), committed BEFORE the page.
 *
 * Live metrics come from the database; evaluation runs come from the run files and sit in their own section, below
 * the live row, never in it. "Resolution rate" does not appear: the spec never defined it (L20). With no data a
 * section shows an honest empty state, never a zero standing in for a missing median or percentile.
 *
 * Test 1 reads the REAL API (the local stack and the repo's run files), so it is also M70's second killer: no replay
 * may be listed among the runs. Test 2 serves an empty payload to check every empty state.
 */

async function staffSignIn(page: Page) {
  const who = staffLogin();
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(who.email);
  await page.getByLabel("Password").fill(who.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Inbox" })).toBeVisible();
}

async function shot(page: Page, name: string) {
  await page.waitForLoadState("networkidle");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow, `${name}: horizontal scroll`).toBeLessThanOrEqual(0);
  await page.screenshot({ path: `tests/e2e/__screenshots__/${test.info().project.name}/${name}.png`, animations: "disabled", fullPage: true });
}

test("dashboard: live row from the database, eval runs below it from the run files, no resolution rate", async ({ page }) => {
  await staffSignIn(page);
  await page.goto("/console/dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

  const live = page.getByRole("region", { name: "Live metrics" });
  for (const tile of ["Actions, last 24 hours", "Approvals pending", "Median time to approval", "Tokens, last 24 hours", "Unsafe actions, live check"]) {
    await expect(live.getByText(tile, { exact: true })).toBeVisible();
  }
  // the unsafe tile carries its definition, including what it cannot check
  await expect(live.getByText(/cannot be checked live/)).toBeVisible();

  const evals = page.getByRole("region", { name: "Evaluation runs" });
  await expect(evals.getByText("20261114T085006Z")).toBeVisible(); // the adversarial run, from its run file
  await expect(evals.getByText("Latest", { exact: true })).toBeVisible();
  await expect(evals.getByText(/not live data/i)).toBeVisible();
  await expect(evals.getByText(/replay-/)).toHaveCount(0); // replays are re-scorings, not runs (M70)

  // the eval section is below the live row, never inside it
  const [liveBox, evalBox] = [await live.boundingBox(), await evals.boundingBox()];
  expect(liveBox && evalBox && evalBox.y > liveBox.y + liveBox.height - 1).toBe(true);
  await expect(live.getByText("20261114T085006Z")).toHaveCount(0);

  await expect(page.getByText(/resolution rate/i)).toHaveCount(0);
  await shot(page, "30-dashboard");
});

const EMPTY = {
  now: "2026-11-14T12:00:00Z",
  actions_last_24h: { completed: 0, waiting_for_approval: 0, refused: 0 },
  approvals_pending: 0,
  time_to_approval: { median_seconds: null, decisions: 0 },
  tokens: { used_24h: 0, budget: 180000, model: "openai/gpt-oss-120b" },
  unsafe_live: { count: 0, findings: [], definition: "Executed actions in the database that ... cannot be checked live." },
  actions_by_day: Array.from({ length: 14 }, (_, i) => ({ day: `2026-11-${String(i + 1).padStart(2, "0")}`, completed: 0, waiting_for_approval: 0, refused: 0 })),
  approval_outcomes: { approved: 0, rejected: 0, expired: 0, failed_recheck: 0 },
  latency: { p50_ms: null, p95_ms: null, turns: 0, window_days: 7 },
  eval_runs: [],
  eval_unsafe_definition: "Pre-registered per run.",
};

test("dashboard: every section with no data shows an honest empty state, not a zero", async ({ page }) => {
  await page.route("**/v1/staff/dashboard", (route) => route.fulfill({ json: EMPTY }));
  await staffSignIn(page);
  await page.goto("/console/dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

  for (const sentence of [
    "No actions in the last 24 hours",
    "No staff decisions yet",
    "No replies in the last 7 days",
    "No evaluation runs",
    "No actions in the last 14 days",
    "No approval decisions yet",
  ]) {
    await expect(page.getByText(sentence, { exact: true })).toBeVisible();
  }
  // a missing median or percentile is never shown as 0
  const median = page.getByRole("group", { name: "Median time to approval" });
  const latency = page.getByRole("group", { name: "Reply latency, last 7 days" });
  await expect(median.getByText(/^0/)).toHaveCount(0);
  await expect(latency.getByText(/^0/)).toHaveCount(0);
  await shot(page, "31-dashboard-empty");
});
