import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The demo is opened at http://127.0.0.1:3000 (Playwright capture uses it too);
  // Next 16 blocks dev resources from origins it doesn't know.
  allowedDevOrigins: ["127.0.0.1"],
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
