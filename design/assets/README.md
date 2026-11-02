# Saklolo assets

Original vector art for the dashboard: the logo mark and the scenes used for empty,
loading, and error states. It's all hand-authored for Saklolo. Nothing is copied from
`design/reference/`, and the images contain no text or real logos.

These are flat, layered vector scenes for the dark theme, drawn as night scenes. On the light theme, the default, they read as framed images. They don't attempt the
reference's isometric clay style, which the `illustration` skill covers.

## Rebuild

Edit an `.svg` here, then run `npm run assets` in `web/`. The output goes to
`web/public/assets/`.

- Colors are `{{name}}` placeholders, filled from `PALETTE` in
  `web/scripts/build-assets.mjs`: dark token values plus the storm and flood tints.
- `scene-boot.svg` also has `{{rain}}`, `{{shimmer}}`, `{{glowRadius}}`, and
  `{{glowOpacity}}`, filled for each frame of the animated version.
- Rain is seeded, and every drop falls a whole number of screen heights per loop, so
  the 24-frame loop is seamless and a rebuild is repeatable.
- Limits: 60 KB per scene, 400 KB for the animation. The build lowers quality to fit,
  and fails if it can't.
