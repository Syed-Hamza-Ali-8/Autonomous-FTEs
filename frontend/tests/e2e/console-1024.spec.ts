import { execFileSync } from "node:child_process";
import path from "node:path";

import { expect, test, type Locator, type Page } from "@playwright/test";

import { customers, staffLogin } from "./helpers";

/**
 * The staff console at 1024px, light and dark (DECISIONS L5; Phases 5+6 pre-registration section 5). Phase 4's
 * criterion "usable at 1024" was not evidenced; this makes it evidenced or a measured miss. Committed before any
 * console change: it runs against the console as it stands.
 *
 * "Usable at 1024" means, as pre-registered:
 * - no horizontal page scroll;
 * - the queue and the decision panel both visible without overlapping;
 * - the approve and reject dialogs fit the viewport;
 * - the decision controls are reachable by keyboard, with a visible focus indicator.
 *
 * Data as in console.spec.ts: real API output produced model-free by backend/scripts/console_samples.py inside a
 * rolled-back transaction, served by Playwright. No tokens; nothing written.
 */

type Json = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any

function samples(customerId: string): Json {
  const out = execFileSync("uv", ["run", "python", "scripts/console_samples.py", customerId], {
    cwd: path.resolve(__dirname, "../../../backend"),
    encoding: "utf8",
  });
  return (JSON.parse(out) as Json).staff;
}

async function shot(page: Page, name: string) {
  await page.waitForLoadState("networkidle");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow, `${name}: horizontal scroll`).toBeLessThanOrEqual(0);
  await page.screenshot({ path: `tests/e2e/__screenshots__/${test.info().project.name}/${name}.png`, animations: "disabled" });
}

async function serveStaff(page: Page, s: Json) {
  await page.route("**/v1/staff/approvals", (route) => route.fulfill({ json: s.queue }));
  await page.route(/\/v1\/staff\/approvals\/ACT-\d+$/, (route) => {
    const ref = route.request().url().split("/").pop()!;
    return s.details[ref] ? route.fulfill({ json: s.details[ref] }) : route.fulfill({ status: 404, json: { error: "not_found" } });
  });
}

async function box(locator: Locator) {
  const b = await locator.boundingBox();
  expect(b, "element has a layout box").not.toBeNull();
  return b!;
}

const overlaps = (a: { x: number; y: number; width: number; height: number }, b: typeof a) =>
  a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;

async function fitsViewport(page: Page, locator: Locator) {
  const b = await box(locator);
  const vp = page.viewportSize()!;
  expect(b.x, "dialog left edge").toBeGreaterThanOrEqual(0);
  expect(b.y, "dialog top edge").toBeGreaterThanOrEqual(0);
  expect(b.x + b.width, "dialog right edge").toBeLessThanOrEqual(vp.width);
  expect(b.y + b.height, "dialog bottom edge").toBeLessThanOrEqual(vp.height);
}

test.describe.configure({ timeout: 60_000 });
let staff: Json;
test.beforeAll(() => {
  test.setTimeout(120_000);
  staff = samples(customers()[0].customer_id);
});

test("console at 1024: no horizontal scroll, queue and decision panel side by side, dialogs fit, keyboard focus", async ({ page }) => {
  await serveStaff(page, staff);
  const who = staffLogin();
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(who.email);
  await page.getByLabel("Password").fill(who.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Inbox" })).toBeVisible();

  const queue = page.getByRole("list", { name: "Queue" });
  await expect(queue.getByRole("button").first()).toBeVisible();
  await shot(page, "20-console-inbox");

  // Open the first request: the queue stays visible and the decision panel appears beside it, not over it.
  await queue.getByRole("button").first().click();
  const checklist = page.getByRole("list", { name: "Policy checklist" });
  const decide = page.getByRole("group", { name: "Decide" });
  await expect(checklist).toBeVisible();
  await expect(decide).toBeInViewport();
  await expect(queue).toBeVisible();
  expect(overlaps(await box(queue), await box(checklist)), "queue and decision panel overlap").toBe(false);
  await shot(page, "21-console-detail");

  // Keyboard: Tab reaches the Approve control and its focus is visible.
  const approveButton = page.getByRole("button", { name: /^Approve/ }).first();
  let reached = false;
  for (let i = 0; i < 60 && !reached; i++) {
    await page.keyboard.press("Tab");
    reached = await approveButton.evaluate((el) => el === document.activeElement);
  }
  expect(reached, "Approve is reachable by Tab").toBe(true);
  const ring = await approveButton.evaluate((el) => {
    const s = getComputedStyle(el);
    return { outline: s.outlineStyle !== "none" && s.outlineWidth !== "0px", shadow: s.boxShadow !== "none" };
  });
  expect(ring.outline || ring.shadow, "focused Approve shows a focus indicator").toBe(true);

  // Both confirm dialogs fit inside the 1024 viewport.
  await page.keyboard.press("Enter");
  const approve = page.getByRole("alertdialog");
  await expect(approve).toBeVisible();
  await fitsViewport(page, approve);
  await shot(page, "22-console-approve-dialog");
  await approve.getByRole("button", { name: "Cancel" }).click();
  await page.getByRole("button", { name: /^Reject/ }).first().click();
  const reject = page.getByRole("alertdialog");
  await expect(reject).toBeVisible();
  await fitsViewport(page, reject);
  await shot(page, "23-console-reject-dialog");
});
