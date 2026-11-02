# Badge

A filled pill for a priority level, always with its text. `status-*` colors mean
priority only (R5), and they're exempt from the one accent rule. Use `PriorityBadge`
in screens; `Badge` is its base.

**Don't use it for** flags or message kinds: use `Text` with `caption-bold`.

| Prop       | Values                                         | Default  |
| ---------- | ---------------------------------------------- | -------- |
| `tone`     | `critical`, `high`, `moderate`, `info`, `none` | required |
| `urgent`   | critical pulse (R21)                           | off      |
| `testId`   | `data-testid`                                  | none     |
| `priority` | `data-priority`                                | none     |

Good: `<Badge tone="critical">P1 Critical</Badge>`

Bad: `<Badge tone="critical">kept for review</Badge>`, which reads as P1.
