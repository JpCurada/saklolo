// The UI gate: `npm run ui:check`. Used by the pre-commit hook and CI.
// Extra arguments go to Playwright, e.g. `npm run ui:check -- --update-snapshots`.
import { spawnSync } from "node:child_process";

// Legacy lint warnings allowed (eslint.config.mjs). Lower this as files are migrated;
// never raise it. New files have no allowance: their violations are errors.
const LEGACY_WARNING_CAP = 0;

// Screenshots cover the demo tools too, so the checked build has them on.
process.env.NEXT_PUBLIC_DEMO_MODE ??= "true";

const extra = process.argv.slice(2).join(" ");
const steps = [
  ["Tokens and WCAG AA contrast", "npm run -s tokens"],
  ["Lint", `npx eslint --max-warnings ${LEGACY_WARNING_CAP}`],
  ["Types", "npm run -s typecheck"],
  ["Build", "npm run -s build"],
  ["Screenshots and visual regression", `npx playwright test ${extra}`],
];

for (const [name, command] of steps) {
  console.log(`\n== ${name}`);
  const { status } = spawnSync(command, { shell: true, stdio: "inherit" });
  if (status !== 0) {
    console.error(`\nui:check failed at: ${name}`);
    process.exit(1);
  }
}
console.log("\nui:check passed");
