# Icon

A 24-grid line icon drawn in `currentColor`, so it follows the text color around it.

**Don't use it for** a status on its own: pair it with text (R6). Scenes and the logo
are images in `public/assets`, not icons.

| Prop    | Values                                                    | Default  |
| ------- | --------------------------------------------------------- | -------- |
| `name`  | see `IconName`                                            | required |
| `label` | accessible name; hidden from screen readers when left out | none     |
| `size`  | `sm` (16px), `md` (24px)                                  | `sm`     |

Good: `<Icon name="map-pin" /> <Text>Malanday</Text>`

Bad: `<Icon name="alert" />` as the only sign of a critical case.
