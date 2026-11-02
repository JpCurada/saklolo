import { defineConfig } from "@playwright/test";

const PORT = 3100;

// Visual checks for ui:check. The API is mocked (tests/visual/fixtures.ts), so no AWS
// is needed. Baselines depend on the OS's font rendering, hence {platform}.
export default defineConfig({
  testDir: "./tests/visual",
  outputDir: "./test-results",
  snapshotPathTemplate: "../design/screenshots/baseline/{platform}/{arg}{ext}",
  workers: 1,
  reporter: "line",
  // An absolute limit: a ratio of a 1080p page lets a whole line of text change unnoticed.
  expect: { toHaveScreenshot: { maxDiffPixels: 20, animations: "disabled" } },
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    viewport: { width: 1920, height: 1080 },
    // Reduced motion serves the static boot image, which keeps screenshots stable.
    contextOptions: { reducedMotion: "reduce" },
  },
  webServer: {
    command: `npx next start --port ${PORT}`,
    url: `http://127.0.0.1:${PORT}`,
    reuseExistingServer: false,
  },
});
