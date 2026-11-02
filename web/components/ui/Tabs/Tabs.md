# Tabs

Switches views inside a panel. Arrow keys, Home, and End move between tabs.

**Don't use it for** actions: use `Button`.

| Prop       | Values                           | Default  |
| ---------- | -------------------------------- | -------- |
| `label`    | accessible name for the tab list | required |
| `tabs`     | `{ id, label, testId? }[]`       | required |
| `active`   | the selected `id`                | required |
| `onChange` | called with the new `id`         | required |

Good: `<Tabs label="Lanes" tabs={lanes} active={lane} onChange={setLane} />`

Bad: tabs with no keyboard support.
