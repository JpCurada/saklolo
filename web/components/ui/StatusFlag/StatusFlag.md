# StatusFlag

A case flag, such as "Corroborated" or "Needs review". Neutral, because color means
priority (R5), so an icon and the text tell flags apart. Goes in a `StatusFlagList`.

**Don't use it for** priority: use `PriorityBadge`.

| Prop       | Values                     | Default  |
| ---------- | -------------------------- | -------- |
| `flag`     | the value for `data-badge` | required |
| `icon`     | a small icon               | none     |
| `children` | the label                  | required |

Good: `<StatusFlag flag="corroborated" icon={<Icon name="check" />}>Corroborated</StatusFlag>`

Bad: a green `Badge`.
