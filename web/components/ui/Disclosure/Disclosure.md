# Disclosure

A section of a panel that folds to its header: "Decisions (2)", "Messages in this case (3)".

**Don't use it for** what a dispatcher needs to decide at a glance, such as the priority,
the summary or the reason: those stay visible.

| Prop          | Values                                      | Default  |
| ------------- | ------------------------------------------- | -------- |
| `title`       | the section name, sentence case             | required |
| `meta`        | after the title: a count or a short summary | none     |
| `defaultOpen` | open on first render                        | `false`  |
| `testId`      | `data-testid` on the `<details>`            | none     |
