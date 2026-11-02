# Bubble

One message on a simulated resident phone (`/resident`), in that phone's skin (R23).

**Don't use it for** dispatcher UI. Messages in a case use `SourceList`.

| Prop        | Values                                          | Default  |
| ----------- | ----------------------------------------------- | -------- |
| `direction` | `out` (resident sent), `in` (resident received) | required |
| `skin`      | `sms`, `telegram`, `messenger`                  | required |
| `time`      | shown inside the bubble                         | none     |
| `delivered` | double ticks after the time                     | off      |
| `avatar`    | the contact's initial beside a received message | none     |
| `testId`    | `data-testid`                                   | none     |
| `lang`      | language of the message                         | none     |

Needs a column flex parent, because `self-end` and `self-start` place it.

Good: `<Bubble direction="out" skin="telegram" time="09:30" lang="fil">Tulong po</Bubble>`

Bad: a bubble with the Telegram logo beside it.
