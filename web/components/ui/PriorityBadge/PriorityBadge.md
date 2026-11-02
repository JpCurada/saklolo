# PriorityBadge

The one way to show a triage priority: `Badge` with the right tone and label.

**Don't use it for** other statuses: use `Badge`.

| Prop       | Values                                 | Default  |
| ---------- | -------------------------------------- | -------- |
| `priority` | `P1`, `P2`, `P3`, `P4`, `null`         | required |
| `urgent`   | pulse, for an unassigned P1 only (R21) | off      |

Good: `<PriorityBadge priority="P1" />`

Bad: `<Badge tone="critical">Urgent</Badge>`, which invents a second label for P1.
