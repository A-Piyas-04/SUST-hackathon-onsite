import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";

// Pin the workspace root to this app so the multiple-lockfile inference warning
// (root package-lock.json vs frontend/package-lock.json) does not fire.
const nextConfig: NextConfig = {
  // Emit the minimal Node.js server and traced runtime dependencies used by
  // the production Docker image.
  output: "standalone",
  turbopack: {
    root: dirname(fileURLToPath(import.meta.url)),
  },
};

export default nextConfig;
