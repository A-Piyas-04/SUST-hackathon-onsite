# Frontend

Next.js role-aware web interface for the Multi-Provider Agent Liquidity & Coordination Platform.

Project-wide setup and the judged walkthrough are in the [root README](../README.md) and [demo guide](../docs/demo-guide.md).

## Run locally

```powershell
npm install
npm run dev
```

Open <http://localhost:3000>. The Next.js server proxies `/api/*` and `/health` to `API_PROXY_TARGET`, which defaults to `http://localhost:8000` during local development.

## Checks

```powershell
npm run lint
npx tsc --noEmit
npx playwright test
```

The Playwright demo spec requires a migrated, seeded backend. Its current scenario selectors/navigation must be re-verified against the latest UI before it is used as submission evidence.

The frontend never receives database service credentials. Hiding actions in the UI is for clarity; backend authorization and PostgreSQL RLS remain authoritative.
