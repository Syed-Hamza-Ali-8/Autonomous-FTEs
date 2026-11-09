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

type Card = { action: string; state: string; order_id: string | null };

function sampleCards(customerId: string): Card[] {
  const out = execFileSync("uv", ["run", "python", "scripts/action_card_samples.py", customerId], {
    cwd: path.resolve(__dirname, "../../../backend"),
    encoding: "utf8",
  });
  return (JSON.parse(out) as { cards: Card[] }).cards;
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
  const cards = sampleCards(a.customer_id);
  expect(cards.map((c) => c.state)).toEqual(["completed", "waiting_for_approval", "not_allowed"]);

  let turn = 0;
  await page.route("**/v1/conversations/latest", (route) => route.fulfill({ json: null }));
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
});
