# StatCard

A number first, with its label below or beside it. It goes inside a `<dl>`. The number
pops when it changes (R18).

**Don't use it for** text values: use `Tile`.

| Prop       | Values                                 | Default  |
| ---------- | -------------------------------------- | -------- |
| `label`    | what is counted                        | required |
| `value`    | the number                             | required |
| `testId`   | `data-testid`                          | required |
| `compact`  | single row, for the header             | off      |
| `critical` | P1 color, for a count of P1 cases only | off      |

Good: `<StatCard compact critical label="Critical" value={3} testId="stat-critical" />`

Bad: `<StatCard critical label="Needs review" ... />`, which reads as a priority.
