# Tile

One labelled fact inside a panel, such as people or water level. Sits on `surface` as
`canvas`.

**Don't use it for** counts in a summary: use `StatCard`.

| Prop       | Values           | Default  |
| ---------- | ---------------- | -------- |
| `label`    | what the fact is | required |
| `testId`   | `data-testid`    | none     |
| `children` | the value        | required |

Good: `<Tile label="People">5</Tile>`

Bad: a `<div>` with its own background and radius.
