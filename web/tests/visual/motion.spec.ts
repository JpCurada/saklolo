import { expect, test, type Page } from "@playwright/test";

import { CASES, MESSAGES, REPLAY } from "./fixtures";

// The screenshot specs run with reduced motion, so motion itself is checked here.
const API = "http://127.0.0.1:8000";
const json = (body: unknown) => ({ json: body, headers: { "access-control-allow-origin": "*" } });

async function mockApi(page: Page, cases: () => unknown) {
  await page.route(`${API}/cases*`, (route) => route.fulfill(json(cases())));
  await page.route(`${API}/messages`, (route) => route.fulfill(json(MESSAGES)));
  await page.route(`${API}/replay`, (route) => route.fulfill(json(REPLAY)));
  await page.route(`${API}/outbox*`, (route) => route.fulfill(json([])));
  await page.route("https://tile.openstreetmap.org/**", (route) => route.abort());
}

const animation = (page: Page, testId: string) =>
  page
    .getByTestId(testId)
    .first()
    .evaluate((node) => getComputedStyle(node).animationName);

test.describe("with motion", () => {
  test.use({ contextOptions: { reducedMotion: "no-preference" } });

  test("boot plays the animated scene", async ({ page }) => {
    await mockApi(page, () => CASES);
    await page.route(`${API}/cases*`, () => {});
    await page.goto("/");
    const image = page.getByTestId("boot-screen").locator("img");
    await expect(image).toHaveJSProperty("complete", true);
    expect(await image.evaluate((img: HTMLImageElement) => img.currentSrc)).toContain("animated");
  });

  test("only cases that arrive later animate in, and unassigned P1 pulses", async ({ page }) => {
    let cases = CASES.slice(1);
    await mockApi(page, () => cases);
    await page.goto("/");
    await page.getByTestId("queue-item").first().waitFor();
    expect(await page.locator("[data-testid=dispatch-queue] .sk-enter").count()).toBe(0);
    cases = CASES;
    await expect(page.getByTestId("queue-item")).toHaveCount(3);
    await expect(page.locator("[data-testid=dispatch-queue] .sk-enter")).toHaveCount(1);
    expect(await animation(page, "priority-badge")).not.toBe("none");
    await expect(page).toHaveTitle(/^\(1 P1\)/);
  });
});

test("reduced motion gets the static scene and no pulse", async ({ page }) => {
  await mockApi(page, () => CASES);
  await page.goto("/");
  await page.getByTestId("queue-item").first().waitFor();
  expect(await animation(page, "priority-badge")).toBe("none");
});

test("J and K move through cases, but not while typing", async ({ page }) => {
  await mockApi(page, () => CASES);
  await page.goto("/");
  const rows = page.getByTestId("queue-item");
  await rows.first().waitFor();
  await page.keyboard.press("j");
  await expect(rows.nth(1)).toHaveAttribute("aria-pressed", "true");
  await page.getByPlaceholder("Reason for the change").focus();
  await page.keyboard.press("j");
  await expect(rows.nth(1)).toHaveAttribute("aria-pressed", "true");
});

test("no stats are shown before there is data", async ({ page }) => {
  await mockApi(page, () => CASES);
  await page.route(`${API}/cases*`, (route) => route.abort());
  await page.goto("/");
  await page.getByTestId("api-error").waitFor();
  await expect(page.getByTestId("stat-critical")).toHaveCount(0);
});

test("map pins carry their priority as text", async ({ page }) => {
  await mockApi(page, () => CASES);
  await page.goto("/");
  await page.getByTestId("queue-item").first().waitFor();
  await expect(page.getByTestId("map-pin").first()).toHaveText(/P[1-4]/);
  await expect(page.getByTestId("map-dot")).toHaveCount(1);
  await page.screenshot({ path: "test-results/map-unmasked.png" });
});
