# ListRow

One row of a dense list: a metadata line, then the content. Rows are separated by
space, not divider lines (R14).

**Don't use it for** clickable rows yet: add a variant when `QueueItem` migrates.

| Prop       | Values                                | Default  |
| ---------- | ------------------------------------- | -------- |
| `testId`   | `data-testid`                         | required |
| `meta`     | small facts above the content         | required |
| `trailing` | pinned to the end of the meta line    | none     |
| `onSelect` | makes the row a button                | none     |
| `selected` | tint; sets `aria-pressed`             | `false`  |
| `caseId`   | `data-case-id`                        | none     |
| `enter`    | slide in, for a row that just arrived | off      |
| `children` | row content                           | required |

Good: `<ListRow testId="feed-item" meta={<Text variant="caption">9:30 AM</Text>}>...</ListRow>`

Bad: `<li className="border-b ...">`
