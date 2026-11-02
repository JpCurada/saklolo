# web

Next.js dispatcher dashboard: queue, human review lane, case detail with map,
phone simulator, live message feed, and replay controls. Built for 1920×1080.
Rules: [typescript/web](../.agents/rules/typescript-web.md). Skill: `web-ui`.

This is Next.js 16: read [AGENTS.md](AGENTS.md) before changing framework code.

## Run

The dashboard needs the demo API on port 8000 (`make demo` from the repo root).

```bash
npm install
npm run build && npx next start --port 3000
```

Open <http://127.0.0.1:3000>. Set `NEXT_PUBLIC_API_URL` at build time to use
another API address. `npm run dev` also works; on a machine low on memory, its
Turbopack helper processes can fail to start (exit code `0xc0000142`), and the
production build avoids that.

## Layout

```
app/          the one route; a thin page
components/   presentational: PriorityBadge, CaseBadges, Panel
features/     dashboard, queue, case-detail, simulator, replay, feed
lib/api/      typed client; types generated from the API schema
lib/          usePolling (every 2 seconds), display helpers
scripts/      copies MapLibre's web worker into public/
```

API types are generated, never hand-written. After changing the API, run
`make api-types` from the repo root.

## Test IDs for video capture

Playwright specs in `video/capture/` select by these `data-testid` values only.

| Area               | IDs                                                                                                                                  |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Header             | `app-header`, `logo`, `stat-open`, `stat-critical`, `stat-review`, `stat-awaiting`                                                   |
| Replay             | `replay-controls`, `sped-up-label`, `replay-speed`, `replay-start`, `replay-stop`, `replay-status`                                   |
| Queue              | `dispatch-queue`, `queue-tab`, `review-tab`, `queue-list`, `review-lane`, `queue-item` (`data-case-id`)                              |
| Any case row       | `priority-badge` (`data-priority`), `case-summary`, `case-reason`, `case-badges`, `badge` (`data-badge`)                             |
| Case detail        | `case-detail`, `case-status`, `case-facts`, `case-location`, `source-list`, `source-item`, `source-original`, `source-summary`       |
| Dispatcher actions | `dispatch-actions`, `assign-team`, `assign-button`, `override-priority`, `override-reason`, `override-button`, `confirm-safe-button` |
| Map                | `case-map`, `map-pin` (selected case), `map-dot` (`data-case-id`)                                                                    |
| Phone              | `phone-simulator`, `phone-sender`, `phone-thread`, `phone-message` (`data-direction`), `phone-input`, `phone-send`                   |
| Feed               | `message-feed`, `feed-item`                                                                                                          |
| Errors             | `api-error`                                                                                                                          |
