import { expect, test } from "@playwright/test";

import { customers, signIn, signOut } from "./helpers";

/**
 * Owner gate item (Phase 1): two customers on the same browser tab never see each other's data,
 * including anything left in the TanStack cache after sign-out (CLAUDE.md security rules).
 */
test("two customers in one tab never see each other's orders, even after sign-out", async ({ page }) => {
  const [a, b] = customers();
  const leak = new Set([...a.order_ids].filter((id) => !b.order_ids.includes(id)));

  // A signs in and loads their list and one order detail (client-side navigation fills the cache).
  await signIn(page, a);
  for (const id of a.order_ids) await expect(page.getByText(id, { exact: true })).toBeVisible();
  for (const id of b.order_ids) await expect(page.getByText(id, { exact: true })).toHaveCount(0);
  await page.getByRole("link", { name: new RegExp(a.featured_order) }).click();
  await expect(page.getByRole("heading", { name: `Order ${a.featured_order}` })).toBeVisible();

  // From here on, record any appearance of A's order ids in the DOM, even for a single frame.
  await page.evaluate((ids) => {
    const seen: string[] = [];
    (window as unknown as { __leaks: string[] }).__leaks = seen;
    const scan = () => {
      const text = document.body.innerText;
      for (const id of ids) if (text.includes(id)) seen.push(id);
    };
    new MutationObserver(scan).observe(document.body, { subtree: true, childList: true, characterData: true });
  }, [...leak]);

  await page.getByRole("navigation", { name: "Main" }).getByRole("link", { name: "My orders" }).click();
  await signOut(page);
  // Watching starts once A's pages are gone; the sign-in page must hold nothing of A's.
  await page.evaluate(() => ((window as unknown as { __leaks: string[] }).__leaks.length = 0));

  // Nothing per-user survives in browser storage either.
  const storage = await page.evaluate(() => ({
    local: Object.keys(localStorage),
    session: Object.keys(sessionStorage),
    dump: JSON.stringify({ ...localStorage, ...sessionStorage }),
  }));
  expect(storage.local.filter((k) => k.startsWith("sb-"))).toEqual([]);
  for (const id of leak) expect(storage.dump).not.toContain(id);

  // B signs in IN THE SAME TAB (no reload, same JS heap) and browses.
  await page.getByLabel("Email").fill(b.email);
  await page.getByLabel("Password").fill(b.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "My orders" })).toBeVisible();
  for (const id of b.order_ids) await expect(page.getByText(id, { exact: true })).toBeVisible();
  await page.getByRole("link", { name: new RegExp(b.featured_order) }).click();
  await expect(page.getByRole("heading", { name: `Order ${b.featured_order}` })).toBeVisible();
  await page.getByRole("navigation", { name: "Main" }).getByRole("link", { name: "Support" }).click();
  await expect(page.getByRole("heading", { name: "Support" })).toBeVisible();

  const leaks = await page.evaluate(() => (window as unknown as { __leaks: string[] }).__leaks);
  expect(leaks, "A's order ids appeared while B was signed in").toEqual([]);

  // B deep-links to A's order: same "not found" as an order that doesn't exist.
  await page.goto(`/orders/${a.featured_order}`);
  await expect(page.getByRole("heading", { name: "Order not found" })).toBeVisible();
  const foreign = await page.locator("main").innerText();
  await page.goto("/orders/ORD-9999");
  await expect(page.getByRole("heading", { name: "Order not found" })).toBeVisible();
  const missing = await page.locator("main").innerText();
  expect(foreign.replace(a.featured_order, "ID")).toBe(missing.replace("ORD-9999", "ID"));
});
