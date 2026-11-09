import { defineConfig, devices } from "@playwright/test";

// Runs against the LOCAL stack only (invariant 20). Playwright starts the API and a production build
// of the web app itself and stops them afterwards; nothing is left running in the background.
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  globalSetup: "./tests/e2e/global-setup.ts",
  globalTeardown: "./tests/e2e/global-teardown.ts",
  use: { baseURL: "http://localhost:3000", trace: "retain-on-failure" },
  webServer: [
    {
      command: "uv run uvicorn tollgate.main:app --host 127.0.0.1 --port 8000",
      cwd: "../backend",
      url: "http://127.0.0.1:8000/healthz",
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: "npm run build && npm run start -- --port 3000",
      url: "http://localhost:3000/sign-in",
      reuseExistingServer: false,
      timeout: 240_000,
    },
  ],
  projects: [
    { name: "isolation", testMatch: /isolation\.spec\.ts/, use: { ...devices["Desktop Chrome"] } },
    {
      name: "desktop-light",
      testMatch: /(screenshots|action-cards)\.spec\.ts/,
      use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 }, colorScheme: "light" },
    },
    {
      name: "desktop-dark",
      testMatch: /(screenshots|action-cards)\.spec\.ts/,
      use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 }, colorScheme: "dark" },
    },
    {
      name: "mobile-light",
      testMatch: /(screenshots|action-cards)\.spec\.ts/,
      use: { ...devices["Pixel 7"], viewport: { width: 390, height: 844 }, colorScheme: "light" },
    },
    {
      name: "mobile-dark",
      testMatch: /(screenshots|action-cards)\.spec\.ts/,
      use: { ...devices["Pixel 7"], viewport: { width: 390, height: 844 }, colorScheme: "dark" },
    },
  ],
});
