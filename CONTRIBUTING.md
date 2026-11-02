# Contributing

Thanks for helping. Saklolo handles rescue requests, so a few rules matter more than
usual.

## Rules that never bend

- A human decides. Nothing may close a case, dismiss a message, or tell a resident help
  is coming without a dispatcher.
- Never drop a message. Doubtful ones are flagged and kept.
- A change that lowers Critical recall doesn't ship.
- Synthetic data only. Never add real names, phone numbers, or posts.

## Getting started

```bash
make install
make hooks       # run the UI check before commits
make test
make ui-check    # after any UI change
```

`make demo-offline` and `make demo-web` run everything without an AWS account.

## Commits

Use `type(scope): description`, for example `fix(agents): keep a sender's second
household`. Branch from `dev` and open pull requests against `dev`.

## Where to read next

[Architecture](docs/architecture.md), [triage rubric](docs/triage-rubric.md),
[design rules](design/DESIGN.md), and the [decision records](docs/adr/).
