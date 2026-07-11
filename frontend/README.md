# Frontend shell (Phase 2)

Minimal Next.js scaffold for the Multi-Provider Agent Liquidity Platform. Feature UI is deferred to Phase 6.

## Setup

```bash
npm install
npm run dev
```

Open http://localhost:3000 — API calls are same-origin and proxied by the Next server to the backend (`API_PROXY_TARGET`, default `http://localhost:8000` in dev). Set `NEXT_PUBLIC_API_BASE_URL` only when browsers should call a separately exposed backend origin directly.

Ensure the backend is running (`cd ../backend && make server`) and migrations/seeds are applied.
