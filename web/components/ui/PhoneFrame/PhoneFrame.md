# PhoneFrame

A simulated resident phone on `/resident`, in the look of SMS, Telegram, or Messenger
(R23): a status bar with a notch, the app's chat header and call icons, the thread,
the message box, and the home bar. It never shows an app's logo.

**Don't use it for** anything a dispatcher works in.

| Prop       | Values                                                        | Default  |
| ---------- | ------------------------------------------------------------- | -------- |
| `skin`     | `sms`, `telegram`, `messenger`                                | required |
| `contact`  | name in the chat header                                       | required |
| `status`   | line under the name                                           | required |
| `label`    | accessible name, for example "Resident phone, Telegram-style" | required |
| `testId`   | `data-testid`                                                 | required |
| `thread`   | the messages                                                  | required |
| `composer` | the message box                                               | required |
| `children` | shown under the phone, such as the simulated sender           | none     |

Good: `<PhoneFrame skin="messenger" contact="Saklolo" status="Active now" ... />`

Bad: a frame with a copied app icon in the header.
