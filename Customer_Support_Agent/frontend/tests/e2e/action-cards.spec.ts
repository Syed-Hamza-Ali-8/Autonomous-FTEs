import { execFileSync } from "node:child_process";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { customers, signIn } from "./helpers";

/**
 * ActionCard screenshots in all three states (spec 13.3, Phase 3), at 1440px and 390px, light and dark.
 *
 * The cards are REAL Action Gateway outcomes for the signed-in customer's own orders, produced model-free by
 * backend/scripts/action_card_samples.py inside a rolled-back transaction (nothing is written). Only the chat
 * transport is stubbed: /v1/chat streams those cards with a short, claim-consistent reply, so the states are
 * deterministic and no tokens are spent. The live model's behaviour is measured by the scored write
 * scenarios, not here.
 */

type Card = { action: string; state: string; order_id: string | null; reference: string | null };
type Samples = { cards: Card[]; records: Record<string, unknown> };

function samples(customerId: string): Samples {
  const out = execFileSync("uv", ["run", "python", "scripts/action_card_samples.py", customerId], {
    cwd: path.resolve(__dirname, "../../../backend"),
    encoding: "utf8",
  });
  return JSON.parse(out) as Samples;
}

const ASK: Record<string, (o: string | null) => string> = {
  update_shipping_address: (o) => `Please send ${o} to 14 Garden Road, Lahore instead.`,
  request_refund: (o) => `${o} arrived damaged. Can I get a refund?`,
  issue_store_credit: (o) => `Could I have store credit for ${o}?`,
  cancel_order: (o) => `Can you cancel ${o}?`,
  create_ticket: () => "Please have someone call me about my last delivery.",
};
const SAY: Record<string, (o: string | null) => string> = {
  completed: (o) => `Done: the change to ${o ?? "your request"} has gone through. The details are in the card above.`,
  waiting_for_approval: (o) => `Your request for ${o} is with our support team for a quick review. You'll see the outcome here.`,
  not_allowed: (o) => `I'm sorry, ${o} can't be changed that way. I can open a ticket or pass you to a person if you'd like.`,
};

async function shot(page: Page, name: string) {
  await page.waitForLoadState("networkidle");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow, `${name}: horizontal scroll`).toBeLessThanOrEqual(0);
  await page.screenshot({ path: `tests/e2e/__screenshots__/${test.info().project.name}/${name}.png`, animations: "disabled" });
}

test("ActionCard: completed, waiting for staff approval, not allowed", async ({ page }) => {
  const [a] = customers();
  const { cards, records } = samples(a.customer_id);
  expect(cards.map((c) => c.state)).toEqual(["completed", "waiting_for_approval", "not_allowed"]);

  // What the server would store for these turns: claim-checked replies with their cards, and no progress
  // steps (those are never stored). Served as the "latest conversation" after the reload below.
  const stored: unknown[] = [];
  let turn = 0;
  await page.route("**/v1/conversations/latest", (route) =>
    route.fulfill({ json: stored.length ? { id: "00000000-0000-4000-8000-000000000001", order_id: null, messages: stored } : null }),
  );
  // C2: action records (real gateway rows, read before the samples' rollback), served for the card's lookup.
  await page.route("**/v1/actions/*", (route) => {
    const ref = decodeURIComponent(route.request().url().split("/").pop() ?? "");
    return records[ref] ? route.fulfill({ json: records[ref] }) : route.fulfill({ status: 404, json: { error: "not_found" } });
  });
  await page.route("**/v1/chat", async (route) => {
    const card = cards[turn];
    const now = new Date().toISOString();
    const events = [
      { type: "turn_started", conversation_id: "00000000-0000-4000-8000-000000000001", turn_id: crypto.randomUUID() },
      { type: "progress", label: "Checking your order..." },
      { type: "action", card },
      { type: "reply", message_id: 9000 + turn, text: SAY[card.state](card.order_id), created_at: now },
      { type: "done" },
    ];
    const sent = JSON.parse(route.request().postData() ?? "{}") as { message: string };
    stored.push(
      { id: 8000 + turn, role: "customer", content: sent.message, created_at: now, orders: [], actions: [] },
      { id: 9000 + turn, role: "assistant", content: SAY[card.state](card.order_id), created_at: now, orders: [], actions: [card] },
    );
    turn += 1;
    await route.fulfill({
      status: 200,
      headers: { "content-type": "text/event-stream" },
      body: events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join(""),
    });
  });

  await signIn(page, a);
  await page.goto("/support");
  const names = ["10-action-completed", "11-action-waiting-for-approval", "12-action-not-allowed"];
  const labels = ["Completed", "Waiting for staff approval", "Not allowed"];
  for (const [i, card] of cards.entries()) {
    const box = page.getByLabel("Message", { exact: true });
    await box.fill(ASK[card.action](card.order_id));
    await box.press("Enter");
    const shown = page.getByRole("region").filter({ hasText: labels[i] }).last();
    await expect(shown).toBeVisible();
    await expect(page.getByLabel("Send message")).toBeVisible();
    await shown.scrollIntoViewIfNeeded();
    await shot(page, names[i]);
  }

  // Item 1: the address card shows the resulting address in full, marking what the merge kept.
  const address = page.getByRole("region", { name: /Address change/ }).getByLabel("Delivery address now");
  await expect(address).toContainText("14 Garden Road");
  await expect(address.getByText("(unchanged)")).not.toHaveCount(0);
  // Item 2: the refused card shows its reference like the others.
  await expect(page.getByRole("region", { name: /Not allowed/ })).toContainText(/Reference AUD-\d+/);

  // Progress lines are session-only: after a reload the cards are back, "Checking your order" is not.
  await page.reload();
  await expect(page.getByRole("region").filter({ hasText: "Not allowed" })).toBeVisible();
  await expect(page.getByText("Checking your order")).toHaveCount(0);
});

test("a waiting ActionCard updates in place when staff decide (DECISIONS C2)", async ({ page }) => {
  test.skip(test.info().project.name !== "desktop-light", "behaviour, not layout: one project is enough");
  const [a] = customers();
  const { cards, records } = samples(a.customer_id);
  const waiting = cards.find((c) => c.state === "waiting_for_approval")!;
  let decided = false;
  await page.route("**/v1/conversations/latest", (route) => route.fulfill({ json: null }));
  await page.route("**/v1/actions/*", (route) => {
    const record = records[waiting.reference!] as Record<string, unknown>;
    // The first read finds it waiting; after that, staff have approved it.
    const body = decided ? { ...record, state: "completed" } : record;
    decided = true;
    return route.fulfill({ json: body });
  });
  await page.route("**/v1/chat", (route) =>
    route.fulfill({
      status: 200,
      headers: { "content-type": "text/event-stream" },
      body: [
        { type: "turn_started", conversation_id: "00000000-0000-4000-8000-000000000002", turn_id: crypto.randomUUID() },
        { type: "action", card: waiting },
        { type: "reply", message_id: 9100, text: "It's with our support team for a quick review.", created_at: new Date().toISOString() },
        { type: "done" },
      ].map((e) => `data: ${JSON.stringify(e)}\n\n`).join(""),
    }),
  );
  await signIn(page, a);
  await page.goto("/support");
  await page.getByLabel("Message", { exact: true }).fill("Can I get a refund?");
  await page.getByLabel("Message", { exact: true }).press("Enter");
  const card = page.getByRole("region", { name: /^Refund/ });
  await expect(card).toContainText("Waiting for staff approval");
  await expect(card).toContainText("Completed", { timeout: 25_000 }); // polled (15 s), updated in place
});
