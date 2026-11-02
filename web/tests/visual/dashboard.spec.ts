import { expect, test, type Page } from "@playwright/test";

import { CASES, MESSAGES, REPLAY } from "./fixtures";

const API = "http://127.0.0.1:8000";
const SCREENSHOTS = "../design/screenshots";

async function mockApi(page: Page, cases: unknown = CASES, dispatcher: string | null = "Ana") {
  await page.addInitScript((name) => {
    if (name) localStorage.setItem("saklolo.dispatcher", name);
  }, dispatcher);
  const json = (body: unknown) => ({ json: body, headers: { "access-control-allow-origin": "*" } });
  await page.route(`${API}/cases*`, (route) => route.fulfill(json(cases)));
  await page.route(`${API}/messages`, (route) => route.fulfill(json(MESSAGES)));
  await page.route(`${API}/replay`, (route) => route.fulfill(json(REPLAY)));
  await page.route(`${API}/outbox*`, (route) => route.fulfill(json([])));
  // The map's tiles and style come from the network; the map is masked in screenshots.
  await page.route("https://tiles.openfreemap.org/**", (route) => route.abort());
  await page.route("https://elevation-tiles-prod.s3.amazonaws.com/**", (route) => route.abort());
}

/** Saves the current image for people, then compares it with the baseline. */
async function capture(page: Page, name: string) {
  // Map tiles and pins come from the network and WebGL, so they're excluded.
  const mask = [page.getByTestId("case-map")];
  await page.waitForFunction(() => [...document.images].every((image) => image.complete));
  await page.screenshot({ path: `${SCREENSHOTS}/${name}.png`, mask });
  await expect(page).toHaveScreenshot(`${name}.png`, { mask });
}

/** Full-page captures show how the dispatch workspace stacks at smaller widths. */
async function captureResponsive(page: Page, name: string) {
  const map = page.getByTestId("case-map");
  const options = {
    fullPage: true,
    mask: (await map.count()) > 0 ? [map] : [],
    maskColor: "#f0f0f0",
  };
  await page.waitForFunction(() => [...document.images].every((image) => image.complete));
  await page.screenshot({ path: `${SCREENSHOTS}/${name}.png`, ...options });
  await expect(page).toHaveScreenshot(`${name}.png`, options);
}

test("queue with a selected case", async ({ page }) => {
  await mockApi(page);
  await page.goto("/dispatch");
  await page.getByTestId("queue-item").first().waitFor();
  await capture(page, "dashboard-queue");
});

test("dropdowns and case sections work with keyboard and pointer", async ({ page }) => {
  await mockApi(page);
  await page.goto("/dispatch");
  await page.getByTestId("queue-item").first().waitFor();

  await page.getByTestId("replay-speed").selectOption("600");
  await expect(page.getByTestId("replay-speed")).toHaveValue("600");
  await page.getByTestId("override-priority").selectOption("P2");
  await expect(page.getByTestId("override-priority")).toHaveValue("P2");

  const messages = page.getByTestId("case-messages");
  const messagesHeader = messages.locator(":scope > summary");
  await messagesHeader.click();
  await expect(messages).not.toHaveAttribute("open", "");
  await messagesHeader.focus();
  await page.keyboard.press("Enter");
  await expect(messages).toHaveAttribute("open", "");

  const trace = page.getByTestId("agent-trace");
  await trace.locator("summary").click();
  await expect(trace).toHaveAttribute("open", "");
});

for (const [name, viewport] of [
  ["dashboard-tablet", { width: 1024, height: 768 }],
  ["dashboard-phone", { width: 390, height: 844 }],
] as const) {
  test(`${name} layout`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await mockApi(page);
    await page.goto("/dispatch");
    await page.getByTestId("queue-item").first().waitFor();
    await expect(page.getByTestId("case-detail")).toBeVisible();
    await captureResponsive(page, name);
  });
}

test("resident phones stack on a phone", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page);
  await page.goto("/resident");
  await expect(page.getByTestId("phone-messenger")).toBeVisible();
  await captureResponsive(page, "resident-phones-phone");
});

test("second case selected", async ({ page }) => {
  await mockApi(page);
  await page.goto("/dispatch");
  await page.getByTestId("queue-item").nth(1).click();
  await capture(page, "dashboard-case");
});

test("human review lane", async ({ page }) => {
  await mockApi(page);
  await page.goto("/dispatch");
  await page.getByTestId("review-tab").click();
  await page.getByTestId("review-lane").waitFor();
  await capture(page, "dashboard-review");
});

test("empty queue", async ({ page }) => {
  await mockApi(page, []);
  await page.goto("/dispatch");
  await page.getByText("No open cases").waitFor();
  await capture(page, "dashboard-empty");
});

test("API unavailable", async ({ page }) => {
  await mockApi(page);
  await page.route(`${API}/cases*`, (route) => route.abort());
  await page.goto("/dispatch");
  await page.getByTestId("api-error").waitFor();
  await capture(page, "dashboard-api-error");
});

test("boot screen until the first response", async ({ page }) => {
  await mockApi(page);
  await page.route(`${API}/cases*`, () => {}); // never answers
  await page.goto("/dispatch");
  await page.getByTestId("boot-screen").waitFor();
  await capture(page, "dashboard-boot");
});

test("closing a case takes a deliberate second click", async ({ page }) => {
  await mockApi(page);
  let closed = 0;
  await page.route(`${API}/cases/*/confirm-safe`, (route) => {
    closed += 1;
    return route.fulfill({ json: CASES[0], headers: { "access-control-allow-origin": "*" } });
  });
  await page.goto("/dispatch");
  const close = page.getByTestId("confirm-safe-button");
  await close.click();
  await expect(close).toHaveText("Confirm close");
  expect(closed).toBe(0);
  await capture(page, "dashboard-close-armed");
  await page.getByTestId("confirm-safe-cancel").click();
  await expect(close).not.toHaveText("Confirm close");
  expect(closed).toBe(0);
  await close.click();
  await close.click();
  await expect.poll(() => closed).toBe(1);
});

test("empty review lane", async ({ page }) => {
  await mockApi(
    page,
    CASES.filter((item) => !item.badges.includes("needs_review")),
  );
  await page.goto("/dispatch");
  await page.getByTestId("review-tab").click();
  await page.getByText("Nothing needs review").waitFor();
  await capture(page, "dashboard-review-empty");
});

test("resident phones: an SMS thread with a reply", async ({ page }) => {
  await mockApi(page);
  const headers = { "access-control-allow-origin": "*" };
  await page.route(`${API}/outbox*`, (route) =>
    route.fulfill({
      headers,
      // Like the API: each phone only gets its own replies.
      json:
        new URL(route.request().url()).searchParams.get("recipient") !== "+639000000901"
          ? []
          : [
              {
                recipient: "+639000000901",
                body: "Saan po kayo eksakto? Please send your barangay or a landmark.",
                sent_at: "2026-11-10T01:31:00Z",
              },
            ],
    }),
  );
  await page.route(`${API}/messages`, (route) =>
    route.request().method() === "POST"
      ? route.fulfill({ headers, json: { received_at: "2026-11-10T01:30:00Z" } })
      : route.fallback(),
  );
  await page.goto("/resident");
  const sms = page.getByTestId("phone-sms");
  await sms.getByTestId("phone-input").fill("Tulong po, nasa bubong na kami");
  await sms.getByTestId("phone-send").click();
  await expect(sms.getByTestId("phone-message")).toHaveCount(2);
  await expect(page.getByTestId("simulated-label")).toBeVisible();
  await capture(page, "resident-phones");
});

test("a keyboard double press never closes a case", async ({ page }) => {
  await mockApi(page);
  let closed = 0;
  await page.route(`${API}/cases/*/confirm-safe`, (route) => {
    closed += 1;
    return route.fulfill({ json: CASES[0], headers: { "access-control-allow-origin": "*" } });
  });
  await page.goto("/dispatch");
  const close = page.getByTestId("confirm-safe-button");
  await close.focus();
  await page.keyboard.press("Enter");
  await expect(close).toHaveText("Confirm close");
  await expect(page.getByTestId("confirm-safe-cancel")).toBeFocused();
  // Moving focus is what stops this: keyboard clicks have no click count to guard on.
  await page.keyboard.press("Enter");
  await expect(close).not.toHaveText("Confirm close");
  await expect(close).toBeFocused();

  // A held key: the first press arms, and the repeats land on Cancel, then get ignored.
  await page.keyboard.down("Enter");
  await page.keyboard.down("Enter");
  await page.keyboard.down("Enter");
  await page.keyboard.up("Enter");
  await expect(close).not.toHaveText("Confirm close");
  expect(closed).toBe(0);
});

test("a closed case leaves a record that a person closed it", async ({ page }) => {
  let cases = [CASES[0]];
  await mockApi(page);
  await page.route(`${API}/cases*`, (route) =>
    route.fulfill({ json: cases, headers: { "access-control-allow-origin": "*" } }),
  );
  await page.route(`${API}/cases/*/confirm-safe`, (route) => {
    cases = [];
    return route.fulfill({ json: CASES[0], headers: { "access-control-allow-origin": "*" } });
  });
  await page.goto("/dispatch");
  const close = page.getByTestId("confirm-safe-button");
  await close.click();
  await expect(close).toHaveText("Confirm close");
  await close.click();
  await expect(page.getByTestId("toast")).toHaveText(/Case closed by Ana\./);
  await expect(page.getByText("No case selected")).toBeVisible();
  await expect(close).toHaveCount(0);
});

test("a failed poll keeps the rows and shows no illustration", async ({ page }) => {
  let down = false;
  await mockApi(page);
  await page.route(`${API}/cases*`, (route) =>
    down
      ? route.abort()
      : route.fulfill({ json: CASES, headers: { "access-control-allow-origin": "*" } }),
  );
  await page.goto("/dispatch");
  await page.getByTestId("queue-item").first().waitFor();
  down = true;
  await page.getByTestId("api-error").waitFor();
  await expect(page.getByTestId("queue-item")).toHaveCount(3);
  await expect(page.getByTestId("dispatch-queue").locator("img")).toHaveCount(0);
  await capture(page, "dashboard-api-stale");
});

test("no decisions until a dispatcher starts a shift", async ({ page }) => {
  await mockApi(page, CASES, null);
  const bodies: unknown[] = [];
  await page.route(`${API}/cases/*/assign`, (route) => {
    bodies.push(route.request().postDataJSON());
    return route.fulfill({ json: CASES[0], headers: { "access-control-allow-origin": "*" } });
  });
  await page.goto("/dispatch");
  await page.getByTestId("dispatcher-needed").waitFor();
  await expect(page.getByTestId("assign-button")).toBeDisabled();
  await expect(page.getByTestId("confirm-safe-button")).toBeDisabled();
  await capture(page, "dashboard-no-dispatcher");

  await page.getByTestId("dispatcher-input").fill("  Ben  ");
  await page.getByTestId("dispatcher-start").click();
  await expect(page.getByTestId("dispatcher-name")).toHaveText("Ben");
  await page.getByTestId("assign-button").click();
  await expect.poll(() => bodies).toEqual([{ team: "Team Bravo", dispatcher: "Ben" }]);
  await expect(page.getByTestId("action-confirmation")).toContainText("by Ben");

  await page.reload();
  await expect(page.getByTestId("dispatcher-name")).toHaveText("Ben");
});

test("case history names who decided", async ({ page }) => {
  await mockApi(page);
  await page.goto("/dispatch");
  await page.getByTestId("queue-item").nth(1).click();
  await expect(page.getByTestId("history-item")).toHaveCount(1);
  await expect(page.getByTestId("history-item")).toContainText("Ana");
});

test("each simulated phone sends on its own channel", async ({ page }) => {
  await mockApi(page);
  const sent: unknown[] = [];
  await page.route(`${API}/messages`, (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    sent.push(route.request().postDataJSON());
    return route.fulfill({
      headers: { "access-control-allow-origin": "*" },
      json: { received_at: "2026-11-10T01:30:00Z" },
    });
  });
  await page.goto("/resident");
  for (const phone of ["phone-telegram", "phone-messenger"]) {
    await page.getByTestId(phone).getByTestId("phone-input").fill("tulong po");
    await page.getByTestId(phone).getByTestId("phone-send").click();
  }
  await expect
    .poll(() => sent)
    .toEqual([
      { sender: "telegram:demo-1", text: "tulong po", channel: "telegram" },
      { sender: "messenger:demo-1", text: "tulong po", channel: "messenger" },
    ]);
});

test("the case shows how the agents decided, step by step", async ({ page }) => {
  await mockApi(page);
  await page.goto("/dispatch");
  const trace = page.getByTestId("agent-trace");
  await expect(trace).toHaveCount(1);
  // Folded until asked for: the case reads top-down without it.
  await expect(trace).not.toHaveAttribute("open", "");
  await trace.locator("summary").click();
  await expect(trace).toHaveAttribute("open", "");
  await expect(trace.getByTestId("trace-step")).toHaveCount(8);
  await expect(trace.locator("[data-step=verify]")).toContainText("Check for old posts");
  await expect(trace.locator("[data-step=escalate]")).toHaveAttribute("data-status", "skipped");
  await expect(trace).toContainText("2 model calls");
  await expect(trace.locator("[data-step=dedupe]")).toContainText("Titan embeddings");
  await trace.scrollIntoViewIfNeeded();
  await capture(page, "dashboard-agent-trace");
});

test("an unsure case shows the Swarm that reviewed it", async ({ page }) => {
  await mockApi(page);
  await page.goto("/dispatch");
  await page.getByTestId("queue-item").nth(1).click();
  await page.getByTestId("agent-trace").locator("summary").click();
  const escalate = page.getByTestId("agent-trace").locator("[data-step=escalate]");
  await expect(escalate).toHaveAttribute("data-status", "ran");
  await expect(escalate).toContainText("Second opinion (Swarm)");
  await expect(escalate).toContainText("triage_reviewer → conflict_resolver → triage_reviewer");
  await expect(escalate).toContainText("Strands Swarm");
  await expect(page.getByTestId("agent-trace")).toContainText("3 model calls");
  await page.getByTestId("agent-trace").scrollIntoViewIfNeeded();
  await capture(page, "dashboard-swarm-review");
});
