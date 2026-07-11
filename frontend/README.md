# Frontend shell (Phase 2)

Minimal Next.js scaffold for the Multi-Provider Agent Liquidity Platform. Feature UI is deferred to Phase 6.

## Setup

```bash
npm install
cp .env.local.example .env.local
npm run dev
```

Open http://localhost:3000 — the landing page calls the backend `GET /health` endpoint configured via `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`).

Ensure the backend is running (`cd ../backend && make server`) and migrations/seeds are applied.
