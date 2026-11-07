import fs from "node:fs";

import { expect, type Page } from "@playwright/test";

import { USERS_FILE } from "./global-setup";

export type E2ECustomer = {
  email: string;
  password: string;
  customer_id: string;
  name: string;
  order_ids: string[];
  featured_order: string;
};

export function customers(): [E2ECustomer, E2ECustomer] {
  const data = JSON.parse(fs.readFileSync(USERS_FILE, "utf8")) as { customers: E2ECustomer[] };
  return [data.customers[0], data.customers[1]];
}

export async function signIn(page: Page, who: E2ECustomer) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(who.email);
  await page.getByLabel("Password").fill(who.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "My orders" })).toBeVisible();
}

export async function signOut(page: Page) {
  await page.getByRole("button", { name: "Account menu" }).click();
  await page.getByRole("menuitem", { name: "Sign out" }).click();
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
}
