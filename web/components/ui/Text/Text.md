# Text

Every piece of text, on the type scale (R8) and the three text levels (R7).

**Don't use it for** priority labels: use `PriorityBadge`.

| Prop      | Values                                         | Default |
| --------- | ---------------------------------------------- | ------- |
| `as`      | `span`, `p`, `h2`                              | `span`  |
| `variant` | `body-bold`, `body`, `caption-bold`, `caption` | `body`  |
| `tone`    | `ink`, `muted`, `faint`                        | `ink`   |
| `clamp`   | two-line clamp                                 | off     |
| `lang`    | language of the content                        | none    |

Add `display` and the title variants when a screen needs them.

Good: `<Text as="p" lang="fil" clamp>{message}</Text>`

Bad: `<span className="text-xs text-slate-300">{message}</span>`
