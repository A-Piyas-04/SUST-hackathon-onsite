import { defineConfig, devices } from "@playwright/test";

/**
 * Phase 6 UI end-to-end regression. Requires the backend API running on
 * NEXT_PUBLIC_API_BASE_URL (default http://localhost:8000) with a migrated +
 * seeded database. The frontend dev server is started here (or reused).
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000, // dev-server compiles client chunks on first interaction
  expect: { timeout: 20_000 },
  fullyParallel: false,
  workers: 1,
  retries: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
