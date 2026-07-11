import { test, expect, Page } from "@playwright/test";

/**
 * Drives the thin demo UI through the MVP surfaces. Deterministic behaviour
 * (shortage / anomaly / suppression / case workflow) is asserted; exact figures
 * are left free because each run uses a fresh seed to own its data. Full case
 * lifecycle correctness (ack→note→escalate→review→resolve, immutable evidence,
 * concurrency) is proven exhaustively in the backend Phase 6 E2E suite; here we
 * confirm the same flow is reachable and rendered through the UI.
 */

async function loginAs(page: Page, label: string) {
  await page.goto("/");
  await page.getByRole("button", { name: label }).click();
  await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
}

async function runScenarioWithAnalytics(page: Page, scenarioName: string, analytics: ("liquidity" | "anomaly")[]) {
  await page.getByRole("button", { name: "Scenarios & Faults" }).click();
  const card = page.locator("section").filter({ hasText: scenarioName }).first();
  // Randomize the seed so repeated demo runs never dedup against earlier data.
  await card.locator('button[title*="Randomize"]').click();
  await card.getByRole("button", { name: "Run", exact: true }).click();
  await expect(page.getByText(/Active run/)).toBeVisible();
  await expect(page.getByText(/txns/).first()).toBeVisible();
  for (const a of analytics) {
    const btn = a === "liquidity" ? "Run liquidity analytics" : "Run anomaly analytics";
    await page.getByRole("button", { name: btn }).click();
    const log = a === "liquidity" ? /Liquidity analytics:/ : /Anomaly analytics:/;
    await expect(page.getByText(log)).toBeVisible();
  }
}

test("Scenario A — separated reserves and shared-cash shortage, never blended", async ({ page }) => {
  await loginAs(page, "Management");

  // Dashboard: shared cash + three provider cards, no blended total.
  await expect(page.getByText("Shared physical cash")).toBeVisible();
  await expect(page.getByText("bKash e-money")).toBeVisible();
  await expect(page.getByText("Nagad e-money")).toBeVisible();
  await expect(page.getByText("Rocket e-money")).toBeVisible();
  await expect(page.getByText(/never summed into a blended total/i)).toBeVisible();

  await runScenarioWithAnalytics(page, "Hidden Provider Shortage", ["liquidity"]);

  await page.getByRole("button", { name: "Liquidity", exact: true }).click();
  await expect(page.getByText("Shared physical cash")).toBeVisible();
  await expect(page.getByText(/Confidence:/).first()).toBeVisible();
  await expect(page.getByText(/Shortage/).first()).toBeVisible();
});

test("Scenario B & D — anomaly evidence, localized explanation, reachable case workflow", async ({ page }) => {
  await loginAs(page, "Risk Analyst");
  await runScenarioWithAnalytics(page, "Liquidity Pressure with Unusual Activity", ["anomaly"]);

  // Publish alertable candidates.
  await page.getByRole("button", { name: "Publish alertable candidates" }).click();
  await expect(page.getByText(/Published \d+ alert/)).toBeVisible();

  // Anomaly evidence: structured evidence + prominent benign context.
  await page.getByRole("button", { name: "Anomalies" }).click();
  await expect(page.getByRole("heading", { name: "near identical amounts" }).first()).toBeVisible();
  await expect(page.getByText("Plausible benign context").first()).toBeVisible();
  await expect(page.getByText("Structured evidence").first()).toBeVisible();

  // Alerts: select an alert, read the explanation, toggle to Bangla.
  await page.getByRole("button", { name: "Alerts", exact: true }).click();
  await page.locator("aside, div").getByRole("button").filter({ hasText: /review|Unusual|shortage/ }).first().click();
  await expect(page.getByText("Explanation")).toBeVisible();
  await page.getByRole("button", { name: "বাংলা" }).click();
  await expect(page.getByText("Situation").first()).toBeVisible();

  // Open (or view) the case and confirm the workflow surface renders.
  const openCase = page.getByRole("button", { name: "Open case" });
  const viewCase = page.getByRole("button", { name: "View case" });
  if (await openCase.isVisible().catch(() => false)) await openCase.click();
  else await viewCase.first().click();

  await expect(page.getByText("Case workflow")).toBeVisible();
  await expect(page.getByText("Recommended next step")).toBeVisible();
  await expect(page.getByText("Audit trail")).toBeVisible();
});

test("Scenario C — degraded data suppresses alerts (marked non-alertable)", async ({ page }) => {
  await loginAs(page, "Management");
  await runScenarioWithAnalytics(page, "Data Inconsistency", ["anomaly", "liquidity"]);

  await page.getByRole("button", { name: "Anomalies" }).click();
  await expect(page.getByText(/Suppressed \(degraded data\)/)).toBeVisible();
  await expect(page.getByText(/not an actionable alert/i).first()).toBeVisible();
});

test("Empty states render safely for a provider-scoped identity", async ({ page }) => {
  await loginAs(page, "Provider Ops — Nagad");

  // Deterministic right-pane empty states (independent of list contents).
  await page.getByRole("button", { name: "Cases" }).click();
  await expect(page.getByText("Select a case to manage its lifecycle.")).toBeVisible();

  await page.getByRole("button", { name: "Alerts", exact: true }).click();
  await expect(page.getByText(/Select an alert to view/)).toBeVisible();
});
