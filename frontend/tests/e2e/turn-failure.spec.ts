import { expect, test, type Page } from "@playwright/test";

import { customers, signIn } from "./helpers";

/**
 * Committed BEFORE the code (owner, 2026-11-14). Only the chat transport is stubbed; no tokens are spent.
 *
 * 1-2: when the gateway has acted and the turn then fails (an error event, or a stream that just ends), the card
 *      the gateway produced stays on screen beside a plain error, and no "Retry" is offered: resending could ask
 *      for the same action again. (After a reload, the backend probes tc01-tc06 cover the stored side.)
 * 3:   reply text renders a strict bold/italic subset as React text nodes; raw HTML in a reply is shown as
 *      text and never rendered (model output is not trusted: no Markdown or HTML renderer).
 */

const INTERRUPTED = "Something went wrong while writing the reply. Here is what was done.";
const CONV = "00000000-0000-4000-8000-000000000007";

function card() {
  return {
    action: "escalate_to_human",
    state: "completed",
    order_id: null,
    amount: null,
    reference: "ACT-000777",
    explanation: "A member of our support team will pick this up.",
    at: new Date().toISOString(),
  };
}

async function stub(page: Page, events: unknown[]) {
  await page.route("**/v1/conversations/latest", (route) => route.fulfill({ json: null }));
  await page.route("**/v1/actions/*", (route) => route.fulfill({ status: 404, json: { error: "not_found" } }));
  await page.route("**/v1/chat", (route) =>
    route.fulfill({
      status: 200,
      headers: { "content-type": "text/event-stream" },
      body: events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join(""),
    }),
  );
}

async function send(page: Page, text: string) {
  await signIn(page, customers()[0]);
  await page.goto("/support");
  await page.getByLabel("Message", { exact: true }).fill(text);
  await page.getByLabel("Message", { exact: true }).press("Enter");
}

for (const [name, tail] of [
  ["an error event", [{ type: "error", code: "rate_limited", message: "I'm getting a lot of requests right now. Please try again in a moment.", retry_after_s: 7 }, { type: "done" }]],
  ["a stream that just ends", []],
] as const) {
  test(`a turn that fails after the gateway acted (${name}) keeps the card, with a plain error and no retry`, async ({ page }) => {
    await stub(page, [{ type: "turn_started", conversation_id: CONV, turn_id: crypto.randomUUID() }, { type: "action", card: card() }, ...tail]);
    await send(page, "Please get me a person.");
    await expect(page.getByText(INTERRUPTED)).toBeVisible();
    await expect(page.getByRole("region").filter({ hasText: "Completed" })).toBeVisible();
    await expect(page.getByText("ACT-000777")).toBeVisible();
    await expect(page.getByRole("button", { name: /Retry/ })).toHaveCount(0);
  });
}

test("reply text: bold and italic only; raw HTML in a reply is shown as text and never rendered", async ({ page }) => {
  const dialogs: string[] = [];
  page.on("dialog", (d) => {
    dialogs.push(d.message());
    void d.dismiss();
  });
  const text = '**ORD-1148** has *shipped*. <img src=x onerror="alert(1)"> <b>bold?</b> <script>alert(2)</script>';
  await stub(page, [
    { type: "turn_started", conversation_id: CONV, turn_id: crypto.randomUUID() },
    { type: "reply", message_id: 9300, text, created_at: new Date().toISOString() },
    { type: "done" },
  ]);
  await send(page, "Where is my order?");
  const reply = page.locator("li").filter({ hasText: "has" }).last();
  await expect(reply.locator("strong", { hasText: "ORD-1148" })).toHaveCount(1);
  await expect(reply.locator("em", { hasText: "shipped" })).toHaveCount(1);
  await expect(reply).toContainText('<img src=x onerror="alert(1)">'); // shown as text
  await expect(reply).toContainText("<b>bold?</b>");
  await expect(reply.locator("img, b, script")).toHaveCount(0); // never rendered as elements
  await expect(reply).not.toContainText("**");
  expect(dialogs).toEqual([]);
});
