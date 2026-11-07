import { expect, test, type Page } from "@playwright/test";

import { customers, signIn } from "./helpers";

/**
 * Section 13.6: screenshots of every page at 1440px and 390px, light and dark, for owner review.
 * Saved to tests/e2e/__screenshots__/<project>/. Every page is checked for horizontal scroll, and at
 * mobile widths for fixed or floating elements covering text (owner UI review item 19).
 * The conversation shots need one real model turn; it is spent once, by whichever project runs first.
 * Run on a freshly reset database (`supabase db reset`) so pages show seed data, not leftovers.
 */

const isMobile = (page: Page) => (page.viewportSize()?.width ?? 0) < 768;

// fullPage: false for open dialogs, which cover the viewport while the page behind is scroll-locked.
async function shot(page: Page, name: string, fullPage = true) {
  await page.waitForLoadState("networkidle");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow, `${name}: horizontal scroll`).toBeLessThanOrEqual(0);
  await page.screenshot({
    path: `tests/e2e/__screenshots__/${test.info().project.name}/${name}.png`,
    fullPage,
    animations: "disabled",
  });
}

/** Scroll the whole page a screen at a time; no fixed/sticky element may cover any visible text. */
async function expectNothingCoversText(page: Page, name: string) {
  const height = await page.evaluate(() => document.documentElement.scrollHeight);
  const step = page.viewportSize()!.height;
  for (let y = 0; y < height; y += step) {
    await page.evaluate((top) => window.scrollTo(0, top), y);
    const hits = await page.evaluate(() => {
      const visible = (el: Element) => {
        const s = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        return s.display !== "none" && s.visibility !== "hidden" && r.width > 0 && r.height > 0;
      };
      const floating = [...document.querySelectorAll("body *")].filter((el) => {
        const p = getComputedStyle(el).position;
        return (p === "fixed" || p === "sticky") && visible(el);
      });
      const texts = [...document.querySelectorAll("body *")].filter(
        (el) =>
          visible(el) &&
          [...el.childNodes].some((n) => n.nodeType === Node.TEXT_NODE && n.textContent?.trim()) &&
          !floating.some((f) => f.contains(el)),
      );
      const out: string[] = [];
      for (const f of floating) {
        const a = f.getBoundingClientRect();
        for (const t of texts) {
          const b = t.getBoundingClientRect();
          if (b.bottom <= 0 || b.top >= window.innerHeight) continue;
          if (a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom) {
            out.push(`${f.tagName}.${f.className.toString().slice(0, 40)} covers "${t.textContent?.trim().slice(0, 30)}"`);
          }
        }
      }
      return out;
    });
    expect(hits, `${name}: floating element over text at scrollY=${y}`).toEqual([]);
  }
  await page.evaluate(() => window.scrollTo(0, 0));
}

test("storefront pages", async ({ page }) => {
  test.setTimeout(180_000);
  const [a, b] = customers();

  await page.goto("/sign-in");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await shot(page, "01-sign-in");

  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Enter your email address.")).toBeVisible();
  await expect(page.getByLabel("Email")).toBeFocused();
  await shot(page, "02-sign-in-validation");

  await page.getByLabel("Email").fill(a.email);
  await page.getByLabel("Password").fill("not-the-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await shot(page, "02b-sign-in-error");

  await signIn(page, a);
  await shot(page, "03-orders");
  if (isMobile(page)) await expectNothingCoversText(page, "orders");

  await page.getByRole("radio", { name: "Refunded" }).click();
  await shot(page, "04-orders-filtered");
  await page.getByRole("radio", { name: "All" }).click();

  await page.goto(`/orders/${a.featured_order}`);
  await expect(page.getByRole("heading", { name: `Order ${a.featured_order}` })).toBeVisible();
  await shot(page, "05-order-detail");
  if (isMobile(page)) await expectNothingCoversText(page, "order detail");

  await page.goto(`/orders/${b.featured_order}`);
  await expect(page.getByRole("heading", { name: "Order not found" })).toBeVisible();
  await shot(page, "06-order-not-found");

  // Conversation: create it once with a real turn about A's featured order, then reuse.
  await page.goto("/support");
  const replies = page.locator("main li p").filter({ hasText: "Support:" });
  await expect(page.getByLabel("Message", { exact: true })).toBeVisible();
  if ((await replies.count()) === 0) {
    await page.getByLabel("Message", { exact: true }).fill(`Where is my order ${a.featured_order}?`);
    await page.getByLabel("Message", { exact: true }).press("Enter");
    await expect(page.getByLabel("Stop")).toBeVisible();
    await shot(page, "07-support-working");
    await expect(page.getByLabel("Send message")).toBeVisible({ timeout: 90_000 });
  }
  await expect(replies.last()).toBeVisible();
  await shot(page, "08-support-conversation");

  // Opened from an order: compact order card on top, chips that fit the order's status.
  await page.goto(`/orders/${a.featured_order}`);
  await page.getByRole("button", { name: "Get help with this order" }).click();
  const panel = page.getByRole("dialog", { name: "Support" });
  await expect(panel).toBeVisible();
  await expect(panel.getByRole("link", { name: new RegExp(a.featured_order) })).toBeVisible();
  await expect(panel.getByRole("button", { name: "Something's wrong with it" })).toBeVisible();
  await expect(panel.getByRole("button", { name: /address/i })).toHaveCount(0);
  await shot(page, "09-chat-panel-from-order", false);
});

test("empty and signed-in states for a second customer", async ({ page }) => {
  const [, b] = customers();
  await signIn(page, b);
  await page.goto("/support");
  await expect(page.getByText("How can we help?")).toBeVisible();
  await shot(page, "10-support-empty");
  await page.goto("/orders");
  await page.getByRole("button", { name: "Account menu" }).click();
  await expect(page.getByRole("menuitem", { name: "Sign out" })).toBeVisible();
  await shot(page, "11-account-menu");
});

test("mobile support chat stays usable with the on-screen keyboard open", async ({ page }) => {
  test.skip(!isMobile(page), "mobile layouts only");
  const [, b] = customers();
  await signIn(page, b);
  await page.goto("/support");
  const composer = page.getByLabel("Message", { exact: true });
  await expect(composer).toBeVisible();
  const { width } = page.viewportSize()!;
  // With interactive-widget=resizes-content the keyboard shrinks the layout viewport; emulate that.
  for (const height of [844, 450]) {
    await page.setViewportSize({ width, height });
    await composer.focus();
    const box = await composer.boundingBox();
    expect(box, `composer laid out at height ${height}`).not.toBeNull();
    expect(box!.y + box!.height, `composer inside the viewport at height ${height}`).toBeLessThanOrEqual(height);
    expect(box!.y, `composer not pushed off the top at height ${height}`).toBeGreaterThan(0);
    const scrolls = await page.evaluate(() => document.documentElement.scrollHeight > window.innerHeight);
    expect(scrolls, `page itself does not scroll at height ${height}`).toBe(false);
  }
});
