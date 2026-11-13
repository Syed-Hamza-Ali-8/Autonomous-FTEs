import { execFileSync } from "node:child_process";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { customers, signIn, staffLogin } from "./helpers";

/**
 * Staff console and the Phase 4 customer states (spec 13.4, 13.6), at 1440px and 390px, light and dark.
 *
 * The sign-in, the staff gate and /v1/staff/me are REAL: the seeded support lead (DECISIONS J13). The
 * console's data is REAL API output too, produced model-free by backend/scripts/console_samples.py inside a
 * rolled-back transaction (scripted turns through the real runner, real gateway outcomes and real decisions;
 * nothing is written). Playwright serves those responses, so the screenshots are deterministic and no tokens
 * are spent. The same samples give the customer's closed card, "couldn't complete" card and expired refund row.
 */

type Json = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
type Samples = { staff: Json; customer: Json };

function samples(customerId: string): Samples {
  const out = execFileSync("uv", ["run", "python", "scripts/console_samples.py", customerId], {
    cwd: path.resolve(__dirname, "../../../backend"),
    encoding: "utf8",
  });
  return JSON.parse(out) as Samples;
}


async function shot(page: Page, name: string) {
  await page.waitForLoadState("networkidle");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow, `${name}: horizontal scroll`).toBeLessThanOrEqual(0);
  await page.screenshot({ path: `tests/e2e/__screenshots__/${test.info().project.name}/${name}.png`, animations: "disabled" });
}

/** Serve the sample staff data; decisions answer like the API and leave the decided item off the queue. */
async function serveStaff(page: Page, s: Json, onDecide?: (ref: string, kind: string) => Promise<void>) {
  const decided = new Set<string>();
  await page.route("**/v1/staff/approvals", (route) =>
    route.fulfill({ json: { ...s.queue, items: s.queue.items.filter((i: Json) => !decided.has(i.reference)) } }),
  );
  await page.route(/\/v1\/staff\/approvals\/ACT-\d+$/, (route) => {
    const ref = route.request().url().split("/").pop()!;
    return s.details[ref] ? route.fulfill({ json: s.details[ref] }) : route.fulfill({ status: 404, json: { error: "not_found" } });
  });
  await page.route(/\/v1\/staff\/approvals\/ACT-\d+\/(approve|reject)$/, async (route) => {
    const parts = route.request().url().split("/");
    const [ref, kind] = [parts[parts.length - 2], parts[parts.length - 1]];
    if (onDecide) await onDecide(ref, kind);
    decided.add(ref);
    await route.fulfill({ json: { reference: ref, approval_id: "APR-000900", decision: kind === "approve" ? "approved" : "rejected", reasons: [] } });
  });
  await page.route("**/v1/staff/audit?*", (route) => route.fulfill({ json: s.audit }));
  await page.route(/\/v1\/staff\/conversations\/[0-9a-f-]+$/, (route) => {
    const id = route.request().url().split("/").pop()!;
    return route.fulfill({ json: s.conversations[id] });
  });
}

async function staffSignIn(page: Page) {
  const who = staffLogin();
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(who.email);
  await page.getByLabel("Password").fill(who.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Inbox" })).toBeVisible();
}

const wide = () => test.info().project.name.startsWith("desktop");
const isIncident = (i: Json) => i.risk_tags.some((t: Json) => t.code === "fraud_signal");
/** The inbox's default order, independently stated: security incidents first, then least time left. */
const defaultOrder = (items: Json[]) =>
  [...items].sort((x, y) => Number(isIncident(y)) - Number(isIncident(x)) || x.expires_at.localeCompare(y.expires_at));

// One set of samples per run (generating them takes a few seconds); each test serves what it needs.
test.describe.configure({ timeout: 60_000 });
let data: Samples;
test.beforeAll(() => {
  test.setTimeout(120_000);
  data = samples(customers()[0].customer_id);
});

test("support console: inbox, decision dialogs, audit log, conversation", async ({ page }) => {
  const s = data.staff;
  await serveStaff(page, s);
  await staffSignIn(page);

  const queue = page.getByRole("list", { name: "Queue" });
  await expect(queue.getByRole("button")).toHaveCount(s.queue.items.length);
  // A suspected unauthorised order is a security incident: in the default sort it sits above every other item,
  // although the samples queue it later than older, larger requests.
  const rows = await queue.getByRole("button").allInnerTexts();
  const flagged = rows.map((r) => r.includes("Customer reported a possible unauthorised order"));
  expect(flagged.some(Boolean), "the samples include a fraud-tagged item").toBe(true);
  expect(flagged.indexOf(false), "fraud-tagged items come first").toBeGreaterThan(flagged.lastIndexOf(true));
  expect(defaultOrder(s.queue.items).map((i: Json) => i.reference)[0]).toBe(s.queue.items.find(isIncident).reference);
  // Rows lead with the time left before expiry; the age is secondary.
  await expect(queue.getByRole("button").first()).toContainText(/Expires in \d+[hm]/);
  await expect(queue.getByRole("button").first()).toContainText(/Queued \d+ (minutes|hours) ago/);
  await expect(page.getByRole("link", { name: /Inbox/ })).toContainText(String(s.queue.items.length));
  if (wide()) {
    // Three panes at 1280px and wider: the oldest request opens with its checklist and transcript.
    await expect(page.getByRole("list", { name: "Policy checklist" })).toBeVisible();
    await expect(page.getByRole("list", { name: "Conversation" })).toBeVisible();
    await shot(page, "20-console-inbox");
  } else {
    await shot(page, "20-console-inbox");
    await queue.getByRole("button").first().click();
    await expect(page.getByRole("list", { name: "Policy checklist" })).toBeVisible();
    // The decision is reachable without scrolling the checklist: the action bar sticks to the bottom.
    await expect(page.getByRole("group", { name: "Decide" })).toBeInViewport();
    await shot(page, "21-console-detail");
  }

  // The confirm dialogs show the exact amount; Reject requires a note.
  const first = defaultOrder(s.queue.items)[0];
  await page.getByRole("button", { name: /^Approve/ }).first().click();
  const approve = page.getByRole("alertdialog");
  await expect(approve).toContainText(/exactly \$|exactly Rs/);
  await shot(page, "22-console-approve-dialog");
  await approve.getByRole("button", { name: "Cancel" }).click();
  await page.getByRole("button", { name: /^Reject/ }).first().click();
  const reject = page.getByRole("alertdialog");
  await reject.getByRole("button", { name: "Reject" }).click();
  await expect(reject.getByText("Add a note explaining the rejection.")).toBeVisible();
  await shot(page, "23-console-reject-dialog");
  await reject.getByRole("button", { name: "Cancel" }).click();
  expect(first.reference).toMatch(/^ACT-/);

  // Audit log, its drawer, and the linked read-only conversation.
  await page.goto("/console/audit");
  await expect(page.getByRole("heading", { name: "Audit log" })).toBeVisible();
  await expect(page.getByRole("table")).toContainText("UTC");
  // The column holds the policy verdict; the staff decision is the Outcome column (amendment A6-P4).
  await expect(page.getByRole("columnheader", { name: "Policy" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Decision" })).toHaveCount(0);
  await shot(page, "24-console-audit");
  await page.getByRole("button", { name: /Decision: rejected/ }).first().click();
  const drawer = page.getByRole("dialog");
  await expect(drawer).toContainText("note");
  await shot(page, "25-console-audit-drawer");
  await drawer.getByRole("link", { name: "Open conversation" }).click();
  await expect(page.getByRole("heading", { name: /Conversation/ })).toBeVisible();
  await page.getByText(/Tool trace/).first().click();
  await expect(page.getByText("get_order").first()).toBeVisible();
  await shot(page, "26-console-conversation");
});

test("decisions wait for the server, then move on; J/K/A drive the inbox", async ({ page }) => {
  test.skip(test.info().project.name !== "desktop-light", "behaviour, not layout: one project is enough");
  const s = data.staff;
  let release!: () => void;
  const held = new Promise<void>((r) => (release = r));
  await serveStaff(page, s, () => held);
  await staffSignIn(page);
  const items = defaultOrder(s.queue.items);
  // A CSS locator: an open modal dialog hides the rest of the page from the accessibility tree.
  const current = page.locator('ul[aria-label="Queue"] [aria-current=true]');
  await expect(current).toContainText(items[0].customer_name);
  await page.keyboard.press("j");
  await expect(current).toContainText(items[1].customer_name);
  await page.keyboard.press("k");
  await expect(current).toContainText(items[0].customer_name);
  await page.keyboard.press("a");
  const dialog = page.getByRole("alertdialog");
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: /^Approve/ }).click();
  // Not optimistic: until the server answers, the dialog stays open and the item stays in the queue.
  await expect(dialog.getByRole("button", { name: "Approving…" })).toBeDisabled();
  await expect(current).toContainText(items[0].customer_name);
  release();
  await expect(page.getByText(`Approved ${items[0].reference}`).first()).toBeVisible();
  await expect(dialog).toBeHidden();
  await expect(current).toContainText(items[1].customer_name);
});

test("customer side: a closed card, a couldn't-complete card, an expired refund row", async ({ page }) => {
  const [a] = customers();
  const c = data.customer;
  const now = new Date().toISOString();
  const messages = c.cards.map((card: Json, i: number) => ({
    id: 9100 + i,
    role: "assistant",
    content: "I've passed this to our support team for a quick review. You'll see the outcome here in the chat.",
    created_at: now,
    orders: [],
    actions: [card],
  }));
  await page.route("**/v1/conversations/latest", (route) =>
    route.fulfill({ json: { id: "00000000-0000-4000-8000-000000000002", order_id: null, messages } }),
  );
  await page.route("**/v1/actions/*", (route) => {
    const ref = decodeURIComponent(route.request().url().split("/").pop() ?? "");
    return c.records[ref] ? route.fulfill({ json: c.records[ref] }) : route.fulfill({ status: 404, json: { error: "not_found" } });
  });
  await page.route(`**/v1/orders/${c.order_id}`, (route) => route.fulfill({ json: c.order }));

  await signIn(page, a);
  await page.goto("/support");
  const closed = page.getByRole("region").filter({ hasText: "Closed" }).last();
  const stale = page.getByRole("region").filter({ hasText: "Couldn't complete" }).last();
  await expect(closed).toContainText("wasn't reviewed in time");
  await expect(stale).toContainText("Something about this order changed after you asked");
  await stale.scrollIntoViewIfNeeded();
  await shot(page, "27-cards-closed-and-couldnt-complete");

  await page.goto(`/orders/${c.order_id}`);
  await expect(page.getByText("Closed, not reviewed in time")).toBeVisible();
  await page.getByText("Closed, not reviewed in time").scrollIntoViewIfNeeded();
  await shot(page, "28-order-expired-refund-row");
});
