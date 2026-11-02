# EmptyState

What a panel shows when it has nothing, and what to do next. The only place
illustrations appear (R22).

**Don't use it for** a problem above rows that are still on screen: use a one-line
alert. Don't use it for loading rows either: use `Skeleton`.

| Prop       | Values                                    | Default  |
| ---------- | ----------------------------------------- | -------- |
| `image`    | a file in `public/`                       | required |
| `animated` | animated version; reduced motion skips it | none     |
| `alt`      | empty when decorative                     | required |
| `title`    | the state                                 | required |
| `body`     | what to do next                           | none     |
| `size`     | `md`, or `lg` to fill a panel             | `md`     |
| `testId`   | `data-testid`                             | none     |

Good: `<EmptyState image="/assets/scene-queue-clear.webp" alt="" title="No open cases" body="Send a message or start a replay." />`

Bad: an illustration inside a queue row.
