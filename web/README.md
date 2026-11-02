# web

Next.js dispatcher dashboard: queue, human review lane, case detail with map, and
the live message feed. Built for 1920×1080. In demo mode it adds storm replay and
the resident phones at `/resident`.

This is Next.js 16: check its docs in `node_modules/next/dist/docs/` before changing framework code.

## Run the demo

The dashboard needs the demo API on port 8000. From the repo root:

```bash
make demo        # API
make demo-web    # dashboard on :3000, with replay and /resident
```

Open <http://127.0.0.1:3000>, and <http://127.0.0.1:3000/resident> for the phones.
`npm run dev` also works; on a machine low on memory, its Turbopack helper processes
can fail to start (exit code `0xc0000142`), and the production build avoids that.

## Deploy

`make deploy` from the repo root builds a static export (`STATIC_EXPORT=true`) and
serves it from S3 through CloudFront; see `infra/README.md`. CloudFront sends the
security headers that `next.config.ts` sends under `next start`.

To run it on a Node host instead, settings are read at build time; copy
`.env.example` to `.env.local`.

| Variable | Deployment value |
|---|---|
| `NEXT_PUBLIC_API_URL` | The API's public HTTPS address. Unset, the build warns and uses 127.0.0.1. |
| `NEXT_PUBLIC_DEMO_MODE` | Unset. `true` adds the demo tools, which a dispatcher must never see. |

```bash
npm ci
npm run build
npx next start --port 3000
```

Any Node host that runs `next start` works, including AWS Amplify Hosting with `web`
as the app root. On the API side, add the dashboard's address to
`SAKLOLO_DASHBOARD_ORIGINS`.

Every response carries security headers and `noindex`, and `robots.txt` blocks
crawlers. `/resident` is a 404 outside demo mode.

**Before real users:** the API has no sign-in yet, so anyone who can reach it can
read cases and act on them. Deploy only with synthetic data until Cognito sign-in
is in. A Content Security Policy still needs to be written and tested against the map.

## Layout

```
app/          routes (/, /resident in demo mode), icon
components/ui/  the design system's components
features/     dashboard, queue, case-detail, dispatcher, simulator, replay, feed
lib/api/      typed client; types generated from the API schema
lib/          usePolling (every 2 seconds), display helpers
scripts/      copies MapLibre's web worker into public/
```

API types are generated, never hand-written. After changing the API, run
`make api-types` from the repo root.

## Test IDs for video capture

Playwright specs select by these `data-testid` values only.

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
