# ConfirmDialog

A modal that asks once before an action that's hard to undo, such as signing out.

**Don't use it for** routine actions a dispatcher repeats all night (assign, override):
confirming those slows the queue down.

| Prop            | Values                                                     | Default   |
| --------------- | ---------------------------------------------------------- | --------- |
| `open`          | shown or not                                               | required  |
| `title`, `body` | the question and what happens                              | required  |
| `confirmLabel`  | the action, as a verb: "Sign out"                          | required  |
| `tone`          | `primary`, `danger`                                        | `primary` |
| `onConfirm`     | runs the action; the button shows loading until it settles | required  |
| `onCancel`      | Cancel, Escape                                             | required  |
| `testId`        | also gives `-cancel` and `-confirm`                        | none      |
