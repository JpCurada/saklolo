# web

Next.js dispatcher dashboard, rescue-team page, and phone simulator.
Rules: [typescript/web](../.agents/rules/typescript-web.md). Skill: `web-ui`.

Not scaffolded yet. Create it with:

```bash
cd web
npx create-next-app@latest . --ts --eslint --app --src-dir=false --import-alias "@/*"
npm install -D prettier
```

Then add `format` (`prettier --write .`) and `typecheck` (`tsc --noEmit`) scripts
to `package.json`, since `make fmt` and `make lint` call them.

Planned structure:
```
app/          routes (thin pages)
components/   presentational components
features/     queue/, case-detail/, review-lane/, team/, simulator/
lib/api/      typed API client (types generated from the API schema)
```

Every element the demo video shows needs a stable `data-testid`.
