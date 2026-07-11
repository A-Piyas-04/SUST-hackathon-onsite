# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: demo.spec.ts >> Scenario A — separated reserves and shared-cash shortage, never blended
- Location: e2e\demo.spec.ts:34:5

# Error details

```
Test timeout of 120000ms exceeded.
```

```
Error: locator.click: Test timeout of 120000ms exceeded.
Call log:
  - waiting for locator('section').filter({ hasText: 'Hidden Provider Shortage' }).first().locator('button[title*="Randomize"]')

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - button "Open Next.js Dev Tools" [ref=e7] [cursor=pointer]:
    - img [ref=e8]
  - alert [ref=e11]
  - generic [ref=e12]:
    - banner [ref=e13]:
      - generic [ref=e14]:
        - generic [ref=e15]:
          - paragraph [ref=e16]: Liquidity & Coordination Platform
          - paragraph [ref=e17]: Decision-support demo · http://localhost:8000
        - generic [ref=e18]:
          - generic [ref=e19]:
            - paragraph [ref=e20]: Demo Management
            - paragraph [ref=e21]:
              - generic [ref=e22]: management
              - text: cross-provider
          - generic [ref=e23]:
            - button "English" [ref=e24]
            - button "বাংলা" [ref=e25]
            - button "Banglish" [ref=e26]
          - button "Log out" [ref=e27]
      - navigation [ref=e28]:
        - button "Dashboard" [ref=e29]
        - button "Liquidity" [ref=e30]
        - button "Anomalies" [ref=e31]
        - button "Scenarios & Faults" [active] [ref=e32]
        - button "Alerts" [ref=e33]
        - button "Cases" [ref=e34]
        - button "Notifications" [ref=e35]
    - main [ref=e36]:
      - generic [ref=e37]:
        - generic [ref=e38]: Outlet
        - combobox [ref=e39]:
          - option "OUTLET-001 — Demo Outlet 001 (Market)" [selected]
          - option "OUTLET-002 — Demo Outlet 002 (Riverside)"
      - generic [ref=e40]:
        - generic [ref=e41]:
          - heading "Scenarios & faults" [level=2] [ref=e42]
          - paragraph [ref=e43]: "Drive the deterministic demo: run a scenario, trigger analytics, inject faults, then publish alertable candidates. Seeds are prefilled with each scenario's deterministic default."
        - generic [ref=e44]:
          - generic [ref=e45]:
            - generic [ref=e47]:
              - heading "Normal Operation" [level=3] [ref=e48]
              - paragraph [ref=e49]: Baseline synthetic traffic with healthy feeds.
            - generic [ref=e50]:
              - textbox "Seed for normal" [ref=e51]: "1001"
              - button "🎲" [ref=e52]
              - button "Run" [ref=e53]
          - generic [ref=e54]:
            - generic [ref=e56]:
              - heading "Hidden Shared-Cash Shortage" [level=3] [ref=e57]
              - paragraph [ref=e58]: Heavy bKash cash-out demand depletes shared physical cash while bKash e-money rises.
            - generic [ref=e59]:
              - textbox "Seed for scenario_a" [ref=e60]: "2001"
              - button "🎲" [ref=e61]
              - button "Run" [ref=e62]
          - generic [ref=e63]:
            - generic [ref=e65]:
              - heading "Liquidity Pressure with Unusual Activity" [level=3] [ref=e66]
              - paragraph [ref=e67]: Near-identical repeated amounts alongside falling shared cash.
            - generic [ref=e68]:
              - textbox "Seed for scenario_b" [ref=e69]: "2002"
              - button "🎲" [ref=e70]
              - button "Run" [ref=e71]
          - generic [ref=e72]:
            - generic [ref=e74]:
              - heading "Data Inconsistency" [level=3] [ref=e75]
              - paragraph [ref=e76]: Delayed/conflicting snapshots lower confidence and suppress alerts.
            - generic [ref=e77]:
              - textbox "Seed for scenario_c" [ref=e78]: "2003"
              - button "🎲" [ref=e79]
              - button "Run" [ref=e80]
          - generic [ref=e81]:
            - generic [ref=e83]:
              - heading "Coordinated Response and Closure" [level=3] [ref=e84]
              - paragraph [ref=e85]: An alert is routed and resolved through a case lifecycle.
            - generic [ref=e86]:
              - textbox "Seed for scenario_d" [ref=e87]: "2004"
              - button "🎲" [ref=e88]
              - button "Run" [ref=e89]
```

# Test source

```ts
  1   | import { test, expect, Page } from "@playwright/test";
  2   | 
  3   | /**
  4   |  * Drives the thin demo UI through the MVP surfaces. Deterministic behaviour
  5   |  * (shortage / anomaly / suppression / case workflow) is asserted; exact figures
  6   |  * are left free because each run uses a fresh seed to own its data. Full case
  7   |  * lifecycle correctness (ack→note→escalate→review→resolve, immutable evidence,
  8   |  * concurrency) is proven exhaustively in the backend Phase 6 E2E suite; here we
  9   |  * confirm the same flow is reachable and rendered through the UI.
  10  |  */
  11  | 
  12  | async function loginAs(page: Page, label: string) {
  13  |   await page.goto("/");
  14  |   await page.getByRole("button", { name: label }).click();
  15  |   await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
  16  | }
  17  | 
  18  | async function runScenarioWithAnalytics(page: Page, scenarioName: string, analytics: ("liquidity" | "anomaly")[]) {
  19  |   await page.getByRole("button", { name: "Scenarios & Faults" }).click();
  20  |   const card = page.locator("section").filter({ hasText: scenarioName }).first();
  21  |   // Randomize the seed so repeated demo runs never dedup against earlier data.
> 22  |   await card.locator('button[title*="Randomize"]').click();
      |                                                    ^ Error: locator.click: Test timeout of 120000ms exceeded.
  23  |   await card.getByRole("button", { name: "Run", exact: true }).click();
  24  |   await expect(page.getByText(/Active run/)).toBeVisible();
  25  |   await expect(page.getByText(/txns/).first()).toBeVisible();
  26  |   for (const a of analytics) {
  27  |     const btn = a === "liquidity" ? "Run liquidity analytics" : "Run anomaly analytics";
  28  |     await page.getByRole("button", { name: btn }).click();
  29  |     const log = a === "liquidity" ? /Liquidity analytics:/ : /Anomaly analytics:/;
  30  |     await expect(page.getByText(log)).toBeVisible();
  31  |   }
  32  | }
  33  | 
  34  | test("Scenario A — separated reserves and shared-cash shortage, never blended", async ({ page }) => {
  35  |   await loginAs(page, "Management");
  36  | 
  37  |   // Dashboard: shared cash + three provider cards, no blended total.
  38  |   await expect(page.getByText("Shared physical cash")).toBeVisible();
  39  |   await expect(page.getByText("bKash e-money")).toBeVisible();
  40  |   await expect(page.getByText("Nagad e-money")).toBeVisible();
  41  |   await expect(page.getByText("Rocket e-money")).toBeVisible();
  42  |   await expect(page.getByText(/never summed into a blended total/i)).toBeVisible();
  43  | 
  44  |   await runScenarioWithAnalytics(page, "Hidden Provider Shortage", ["liquidity"]);
  45  | 
  46  |   await page.getByRole("button", { name: "Liquidity", exact: true }).click();
  47  |   await expect(page.getByText("Shared physical cash")).toBeVisible();
  48  |   await expect(page.getByText(/Confidence:/).first()).toBeVisible();
  49  |   await expect(page.getByText(/Shortage/).first()).toBeVisible();
  50  | });
  51  | 
  52  | test("Scenario B & D — anomaly evidence, localized explanation, reachable case workflow", async ({ page }) => {
  53  |   await loginAs(page, "Risk Analyst");
  54  |   await runScenarioWithAnalytics(page, "Liquidity Pressure with Unusual Activity", ["anomaly"]);
  55  | 
  56  |   // Publish alertable candidates.
  57  |   await page.getByRole("button", { name: "Publish alertable candidates" }).click();
  58  |   await expect(page.getByText(/Published \d+ alert/)).toBeVisible();
  59  | 
  60  |   // Anomaly evidence: structured evidence + prominent benign context.
  61  |   await page.getByRole("button", { name: "Anomalies" }).click();
  62  |   await expect(page.getByRole("heading", { name: "near identical amounts" }).first()).toBeVisible();
  63  |   await expect(page.getByText("Plausible benign context").first()).toBeVisible();
  64  |   await expect(page.getByText("Structured evidence").first()).toBeVisible();
  65  | 
  66  |   // Alerts: select an alert, read the explanation, toggle to Bangla.
  67  |   await page.getByRole("button", { name: "Alerts", exact: true }).click();
  68  |   await page.locator("aside, div").getByRole("button").filter({ hasText: /review|Unusual|shortage/ }).first().click();
  69  |   await expect(page.getByText("Explanation")).toBeVisible();
  70  |   await page.getByRole("button", { name: "বাংলা" }).click();
  71  |   await expect(page.getByText("Situation").first()).toBeVisible();
  72  | 
  73  |   // Open (or view) the case and confirm the workflow surface renders.
  74  |   const openCase = page.getByRole("button", { name: "Open case" });
  75  |   const viewCase = page.getByRole("button", { name: "View case" });
  76  |   if (await openCase.isVisible().catch(() => false)) await openCase.click();
  77  |   else await viewCase.first().click();
  78  | 
  79  |   await expect(page.getByText("Case workflow")).toBeVisible();
  80  |   await expect(page.getByText("Recommended next step")).toBeVisible();
  81  |   await expect(page.getByText("Audit trail")).toBeVisible();
  82  | });
  83  | 
  84  | test("Scenario C — degraded data suppresses alerts (marked non-alertable)", async ({ page }) => {
  85  |   await loginAs(page, "Management");
  86  |   await runScenarioWithAnalytics(page, "Data Inconsistency", ["anomaly", "liquidity"]);
  87  | 
  88  |   await page.getByRole("button", { name: "Anomalies" }).click();
  89  |   await expect(page.getByText(/Suppressed \(degraded data\)/)).toBeVisible();
  90  |   await expect(page.getByText(/not an actionable alert/i).first()).toBeVisible();
  91  | });
  92  | 
  93  | test("Empty states render safely for a provider-scoped identity", async ({ page }) => {
  94  |   await loginAs(page, "Provider Ops — Nagad");
  95  | 
  96  |   // Deterministic right-pane empty states (independent of list contents).
  97  |   await page.getByRole("button", { name: "Cases" }).click();
  98  |   await expect(page.getByText("Select a case to manage its lifecycle.")).toBeVisible();
  99  | 
  100 |   await page.getByRole("button", { name: "Alerts", exact: true }).click();
  101 |   await expect(page.getByText(/Select an alert to view/)).toBeVisible();
  102 | });
  103 | 
```