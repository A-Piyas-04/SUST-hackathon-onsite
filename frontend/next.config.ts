import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";

// Pin the workspace root to this app so the multiple-lockfile inference warning
// (root package-lock.json vs frontend/package-lock.json) does not fire.
// Backend the Next server proxies API calls to. Inside docker-compose this is
// the internal service address (http://backend:8000); for `next dev` it is the
// backend running on the host. Resolved when the rewrite manifest is built.
const apiProxyTarget = process.env.API_PROXY_TARGET ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Emit the minimal Node.js server and traced runtime dependencies used by
  // the production Docker image.
  output: "standalone",
  turbopack: {
    root: dirname(fileURLToPath(import.meta.url)),
  },
  // Same-origin proxy for the backend: the browser only ever talks to the
  // frontend origin, so the app works from any host/device that can reach the
  // frontend (no CORS, no hardcoded backend hostname in the client bundle).
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${apiProxyTarget}/api/:path*` },
      { source: "/health", destination: `${apiProxyTarget}/health` },
    ];
  },
};

export default nextConfig;
