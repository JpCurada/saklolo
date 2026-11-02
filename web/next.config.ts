import type { NextConfig } from "next";

if (process.env.NODE_ENV === "production" && !process.env.NEXT_PUBLIC_API_URL) {
  console.warn(
    "NEXT_PUBLIC_API_URL is not set: this build talks to http://127.0.0.1:8000. " +
      "Set it before building for any machine but this one.",
  );
}

// Applied to every response. No CSP yet: MapLibre needs blob: workers and the tile
// server, so a policy must be written and tested against the map first.
const SECURITY_HEADERS = [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  { key: "X-Robots-Tag", value: "noindex, nofollow" },
];

// The deployed dashboard is static files on S3 behind CloudFront, which sends the
// same headers (infra/web.tf); `next start` serves them itself.
const STATIC_EXPORT = process.env.STATIC_EXPORT === "true";

const nextConfig: NextConfig = {
  // The demo is opened at http://127.0.0.1:3000 (Playwright capture uses it too);
  // Next 16 blocks dev resources from origins it doesn't know.
  allowedDevOrigins: ["127.0.0.1"],
  poweredByHeader: false,
  // Export mode serves plain files: no headers(), and no partial prerendering.
  ...(STATIC_EXPORT
    ? { output: "export", trailingSlash: true }
    : {
        cacheComponents: true,
        partialPrefetching: true,
        headers: async () => [{ source: "/:path*", headers: SECURITY_HEADERS }],
      }),
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
