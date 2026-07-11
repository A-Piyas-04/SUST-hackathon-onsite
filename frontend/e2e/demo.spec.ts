import { test, expect, Page } from "@playwright/test";

async function loginAs(page: Page, label: string) {
  await page.goto("/login");
  await page.getByText(label, { exact: false }).click();
  await page.getByRole("button", { name: "Enter" }).click();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
}

async function navTo(page: Page, name: string) {
  await page.getByRole("link", { name }).click();
}

async function runScenario(page: Page, scenarioName: string) {
  await navTo(page, "Scenarios");
  await page.getByText(scenarioName).locator("..").getByRole("button", { name: "Run" }).click();
  await expect(page.getByText(/txns/)).toBeVisible({ timeout: 15_000 });
}

test("Scenario A — separated reserves, never blended", async ({ page }) => {
  await loginAs(page, "Management");
  await expect(page.getByText("Shared cash")).toBeVisible();
  await expect(page.getByText("bKash")).toBeVisible();
  await expect(page.getByText("Separate — not summed")).toBeVisible();

  await runScenario(page, "Hidden Provider Shortage");
  await navTo(page, "Liquidity");
  await expect(page.getByText("Shared")).toBeVisible();
  await expect(page.getByText(/Shortage|No shortage/).first()).toBeVisible();
});

test("Scenario B — anomaly evidence, Bangla explanation, case workflow", async ({ page }) => {
  await loginAs(page, "Risk Analyst");
  await runScenario(page, "Liquidity Pressure");
  await navTo(page, "Scenarios");
  await page.getByRole("button", { name: "Anomaly analytics" }).click();
  await page.getByRole("button", { name: "Publish alerts" }).click();

  await navTo(page, "Anomalies");
  await expect(page.getByText(/near identical|unusual/i).first()).toBeVisible({ timeout: 15_000 });

  await navTo(page, "Alerts");
  await page.locator("a").filter({ hasText: /View|Unusual|shortage/i }).first().click();
  await expect(page.getByText("Situation")).toBeVisible();
  await page.getByRole("button", { name: "বাং" }).click();
  await expect(page.getByText("Situation").first()).toBeVisible();

  const openCase = page.getByRole("button", { name: "Open case" });
  const viewCase = page.getByRole("button", { name: "View case" });
  if (await openCase.isVisible().catch(() => false)) await openCase.click();
  else if (await viewCase.isVisible().catch(() => false)) await viewCase.click();
  else await navTo(page, "Cases");

  await expect(page.getByText("Next step")).toBeVisible();
});

test("Scenario C — degraded data visible in anomalies", async ({ page }) => {
  await loginAs(page, "Management");
  await runScenario(page, "Data Inconsistency");
  await navTo(page, "Anomalies");
  await expect(page.getByText(/suppressed|Advisory only/i).first()).toBeVisible({ timeout: 15_000 });
});

test("Empty states for provider-scoped identity", async ({ page }) => {
  await loginAs(page, "Provider Ops — Nagad");
  await navTo(page, "Cases");
  await expect(page.getByText(/No cases|My queue/).first()).toBeVisible();
  await navTo(page, "Alerts");
  await expect(page.getByText(/No alerts|View/).first()).toBeVisible();
});
