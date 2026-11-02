# Button

Every action. One `primary` per area, because the accent marks the main action (R4).

**Don't use it for** navigation between views: use `Tabs`.

| Prop      | Values                                    | Default   |
| --------- | ----------------------------------------- | --------- |
| `variant` | `primary`, `secondary`, `danger`, `ghost` | `primary` |
| `size`    | `sm`, `md`                                | `md`      |
| `loading` | spinner, blocks repeat presses            | off       |
| `block`   | full width                                | off       |
| `testId`  | `data-testid`                             | none      |
| `ref`     | the button, for moving focus              | none      |

Other button attributes pass through. `className` and `style` don't.

Good: `<Button loading={saving} onClick={assign}>Assign team</Button>`

Bad: `<button className="bg-sky-600 ...">`
