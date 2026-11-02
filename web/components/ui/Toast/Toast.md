# Toast

A stack of short confirmations, announced politely to screen readers. Render one
`Toast` at the top of a screen. The feature owns the list and when items expire.

**Don't use it for** errors the dispatcher must act on: keep those on screen.

| Prop        | Values               | Default  |
| ----------- | -------------------- | -------- |
| `toasts`    | `{ id, message }[]`  | required |
| `onDismiss` | called with the `id` | required |

Good: `<Toast toasts={[{ id: "1", message: "Team Bravo assigned" }]} onDismiss={remove} />`

Bad: a toast for "Can't reach the API".
