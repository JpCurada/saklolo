import { expect, test } from "@playwright/test";

const SCREENSHOTS = "../design/screenshots";

test("the landing page makes no API calls and links to the dashboard", async ({ page }) => {
  const calls: string[] = [];
  page.on("request", (request) => {
    if (request.url().startsWith("http://127.0.0.1:8000")) calls.push(request.url());
  });
  await page.goto("/");
  await expect(page.getByTestId("landing-hero")).toBeVisible();
  await expect(page.getByTestId("landing-steps").locator("li")).toHaveCount(8);
  await expect(page.getByTestId("cta-dispatch")).toHaveAttribute("href", "/dispatch");
  expect(calls).toEqual([]);
});

for (const [name, viewport] of [
  ["landing", { width: 1920, height: 1080 }],
  ["landing-phone", { width: 390, height: 844 }],
] as const) {
  test(`${name} page`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.setViewportSize(viewport);
    await page.goto("/");
    // A full-page image needs the lazy screenshots below the fold too.
    await page.evaluate(() =>
      document.querySelectorAll("img").forEach((image) => (image.loading = "eager")),
    );
    await page.waitForFunction(() =>
      [...document.images].every((image) => image.complete && image.naturalWidth > 0),
    );
    await page.screenshot({ path: `${SCREENSHOTS}/${name}.png`, fullPage: true });
    await expect(page).toHaveScreenshot(`${name}.png`, { fullPage: true });
  });
}
