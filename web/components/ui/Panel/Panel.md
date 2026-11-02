# Panel

A titled, scrolling region of the dashboard. It sits on `canvas` as `surface`, with no
border or shadow (R2).

**Don't use it for** a small grouped fact or a card inside a panel.

| Prop       | Values                            | Default  |
| ---------- | --------------------------------- | -------- |
| `title`    | panel name, in sentence case      | required |
| `testId`   | `data-testid`                     | required |
| `actions`  | controls at the end of the header | none     |
| `children` | panel content                     | required |

Good: `<Panel title="Incoming messages (6)" testId="message-feed">...</Panel>`

Bad: a `<section>` with its own background and radius.
