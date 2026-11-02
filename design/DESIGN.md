# Saklolo design rules

Saklolo uses the visual language of `design/reference/mobile-app-board.png`, adapted for
a dispatcher: warm tone, soft shapes and clear hierarchy, at the density of an ops
screen. The tokens are in `design/tokens/tokens.json`. The current state and the
reasoning are in `design/AUDIT.md`.

We follow the reference's language only. Never copy its name, mascot, or illustrations.

## Rules

Each rule is checked by `design-reviewer`. Lint enforces R1 to R3.

### Values
- **R1. Tokens only.** No raw colors, arbitrary values, or inline styles. If a value is
  missing, add it to `tokens.json`.
- **R2. Depth comes from tone.** Separate layers with `canvas` and `surface`. No shadows;
  `elevation.sheet` is the only exception, for a surface that floats.
- **R3. Compose from `@/components/ui`.** Features arrange components. They don't restyle
  them or rebuild them from raw markup.

### Color
- **R4. One accent.** `accent` marks the primary action and the active item, and nothing
  decorative.
- **R5. Status colors mean priority.** `status-*` tokens are for priority only, so a
  color always reads as one level. They're exempt from R4. Flags such as "suspicious"
  use text weight, not a status color.
- **R6. Color is never the only signal.** Every priority or status shows its text label.
- **R7. Three text levels.** `ink` for content, `ink-muted` for labels, `ink-faint` for
  metadata. Text must meet WCAG AA in both themes.

### Type and hierarchy
- **R8. Use the type scale.** Only `display`, `title-l`, `title-m`, `body-bold`, `body`,
  `caption-bold`, and `caption`.
- **R9. Most important first.** In any row or card the eye lands on the one thing that
  drives a decision. Priority outranks metadata.
- **R10. Sentence case for titles.** Keep uppercase for short codes such as `SMS`.

### Shape and layout
- **R11. Soft shapes.** Panels use `radius-tile`, badges and buttons use `radius-pill`.
  `radius-card` and `radius-sheet` are for roomy screens, such as the rescue team page.
- **R12. Spacing from the 4pt scale.** Use `--sk-space-*` values only.
- **R13. Density before roominess.** The dashboard must show many cases at 1920×1080.
  Don't copy the reference's mobile spacing here.
- **R14. Lists use space, not lines.** No divider lines between rows.

### Safety and copy
- **R15. The human decides.** Nothing may imply a case was closed or dismissed by the
  system. Doubtful items read "kept for review".
- **R16. English interface.** A resident's original message keeps its language, marked
  with `lang`, and sits with its English summary wherever a case is decided.
- **R17. Keep test IDs.** Every `data-testid` stays, because the video capture depends
  on them.

### Motion
- **R18. Motion explains a change.** It shows that something arrived, changed, or
  was confirmed. It never decorates.
- **R19. Respect reduced motion.** Everything in `web/app/motion.css` stops under
  `prefers-reduced-motion`, and the information stays on screen.
- **R20. Nothing flashes.** Repeating signals use `motion-loop`, slower than one cycle
  a second.
- **R21. The critical pulse is for unassigned P1 cases only.** If everything pulses,
  nothing does.

### Illustration
- **R22. Empty states only.** No illustrations in queue or feed rows. They appear only
  when a panel has nothing to show, through `EmptyState`.

### Simulated phones
- **R23. Demo phones look real, but aren't copies.** The phones on `/resident` may use
  the `phone-*` skin tokens to look like SMS, Telegram, and Messenger: layout, bubble
  shape, receipts, and color family. No app logos, icons, wallpapers, or exact brand
  colors. The page says once, outside the phones, that they're demo phones, and the
  video captions them the same way. The skins are exempt from R4 and R11.

## Using tokens

The migration is finished. `web/lib/tokens/tailwind-theme.css` is imported, so Tailwind's
default colors and sizes no longer exist: an off-system class such as `bg-red-500`
generates nothing. The legacy components are gone.

Components in `web/components/ui` read the variables, for example
`bg-(--sk-color-surface)`. Features use the components, and only arrange them with
layout classes. Styling that can't live in a component is in `web/app/`: `layout.css`
for the shell, `map.css` for map pins, and `motion.css` for every animation.
