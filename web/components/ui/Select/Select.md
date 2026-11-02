# Select

A native dropdown for a fixed list of choices. It needs a visible label or an
`aria-label`.

**Don't use it for** free text: use `Input`.

| Prop     | Values        | Default |
| -------- | ------------- | ------- |
| `testId` | `data-testid` | none    |

Other select attributes pass through. `className` and `style` don't.

Good: `<Select aria-label="Priority" value={priority}>...</Select>`

Bad: a custom dropdown built from buttons.
