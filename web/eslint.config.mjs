import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

import { uiPlugin } from "./eslint.ui-rules.mjs";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    files: ["app/**/*.{ts,tsx}", "components/**/*.{ts,tsx}", "features/**/*.{ts,tsx}"],
    plugins: { ui: uiPlugin },
    rules: { "ui/no-off-system-values": "error", "ui/no-style-on-components": "error" },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "test-results/**",
    // Copied from maplibre-gl by scripts/copy-map-worker.mjs.
    "public/**",
  ]),
]);

export default eslintConfig;
