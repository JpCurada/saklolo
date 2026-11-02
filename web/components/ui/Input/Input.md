# Input

A single-line text field. Sits on `surface` as `canvas`. It needs a visible label or an
`aria-label`.

**Don't use it for** a fixed list of choices: use `Select`.

| Prop     | Values                                 | Default |
| -------- | -------------------------------------- | ------- |
| `mono`   | monospace, for codes and phone numbers | off     |
| `testId` | `data-testid`                          | none    |

Other input attributes pass through. `className` and `style` don't.

Good: `<Input aria-label="Team name" value={team} onChange={change} />`

Bad: an input with only a placeholder as its label.
