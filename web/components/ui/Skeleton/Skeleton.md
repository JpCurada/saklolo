# Skeleton

Placeholder lines while content loads for the first time. Hidden from screen readers.

**Don't use it for** a refresh of content already on screen, or for an empty result:
use `EmptyState`.

| Prop    | Values          | Default |
| ------- | --------------- | ------- |
| `lines` | number of lines | `3`     |

Good: `{loading ? <Skeleton /> : <Queue />}`

Bad: a skeleton that replaces cases on every poll.
