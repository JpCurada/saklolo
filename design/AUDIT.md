# UI audit: Saklolo dashboard

Scope: `web/` only, audited at commit `630bb0b`. No code was changed. Theme scope: dark
and light. The reference is `design/reference/mobile-app-board.png`.

## 1. Stack

| Area | Finding |
|---|---|
| Framework | Next.js 16.4 (App Router), React 19, TypeScript strict |
| Styling | Tailwind CSS 4, utility classes only; no CSS modules or CSS-in-JS |
| Theme | No design tokens. `app/globals.css` only maps the Geist fonts; `color-scheme: dark` is forced |
| Tailwind config | None: no `tailwind.config.*`, so the full default palette and scale are available |
| Components | `components/` holds 3 shared parts: `PriorityBadge`, `CaseBadges`, `Panel` |
| Features | `features/` holds 6 folders of screen-specific UI |
| Map | `CaseMap.tsx` writes inline styles, the only place raw values exist |
| Storybook / UI package | None |

## 2. Hardcoded design values

Counts are class occurrences in `.tsx` files.

### Colors

| Role today | Values (uses) | Note |
|---|---|---|
| Page and wells | `bg-slate-950` (8), `bg-slate-950/60` (2) | Same role at two opacities |
| Panels | `bg-slate-900/70` (2), `bg-slate-800` (3) | Layering is already by tone |
| Hover | `hover:bg-slate-800` (3), `hover:bg-slate-800/60` (1) | Near-duplicate |
| Borders | `border-slate-800` (9), `-700` (6), `-600` (3) | Reference uses no visible borders |
| Text | `white` (10), `slate-100` (3), `-200` (3), `-300` (8), `-400` (9), `-500` (8) | **6 levels; 3 are enough** |
| Accent | `bg-sky-600` (5), `hover:bg-sky-500` (2), `ring-sky-500` (1), `text-sky-300` (2) | Used for action, selection, and a badge |
| Priority | `red-600`, `orange-500`, `yellow-300`, `slate-600` | One use each, in `PriorityBadge` |
| Badges | 6 hues at `-300` text and `-400` border | Decorative spread |
| Errors | `text-red-400` (5), `text-red-300` (1), `bg-red-950` (1) | Near-duplicate |
| Label | `bg-amber-400` (1) | Replay notice |

Raw values, all in `CaseMap.tsx`, all duplicating Tailwind colors:

| Raw value | Same as |
|---|---|
| `#dc2626` | `red-600` |
| `#f97316` | `orange-500` |
| `#fde047` | `yellow-300` |
| `#64748b` | `slate-500`, but the badge uses `slate-600`: **a real mismatch** |
| `#94a3b8` | `slate-400` |
| `rgba(15,23,42,.8)` | `slate-900` at 80% |

### Type

| Kind | Values (uses) | Note |
|---|---|---|
| Size | `text-sm` (19), `text-xs` (14), `text-[11px]` (6), `text-lg` (2), `text-xl` (1), `text-[10px]` (1) | **Three sizes within 2px** at the small end |
| Weight | `semibold` (8), `bold` (3), `medium`, `black`, `normal` (1 each) | 5 weights |
| Tracking | `wide` (5), `wider` (2), `tight` (1) | Uppercase labels vary |

The largest text is 20px, so **nothing is number-first** today.

### Radius, spacing, shadow

| Kind | Values (uses) | Note |
|---|---|---|
| Radius | `rounded` (15), `-full` (3), `-lg` (3), `-md` (3), `-2xl` (1) | 5 values; small next to the reference |
| Spacing | `px-2` (10), `gap-2` (9), `px-3` (9), `px-4` (9), `py-2` (8), `gap-3` (6), `py-1.5` (6), `py-1` (5), `py-0.5` (4) | On Tailwind's scale; 6px and 10px are off a 4pt scale |
| Shadow | None | Already matches the reference |
| Fixed sizes | Map pins 22px and 12px, borders 3px and 1px | Inline |

## 3. Recurring elements

| Element | Instances | Inconsistent variants |
|---|---|---|
| Button | 8 | **7**: primary at 3 sizes and 2 shapes, outline at 2 sizes, one conditional green, one tab |
| Text input / select | 6 | **4**: `py-1.5` square, `py-1` square, `py-1` mono, `py-2` pill |
| Card / container | 4 kinds | **4**: `Panel`, `Fact`, source item, header (`lg` and `md` radii) |
| List row | 4 kinds | **4**: queue, feed, source, phone bubble; separators differ |
| Badge | 2 components, 10 styles | **2**: square filled (priority), pill outline (status), plus 3 plain text labels in the feed |
| Tabs | 1 set | 1 |
| Stat | 1 set of 4 | 1 |
| Fact tile | 1 set of 4 | 1 |
| Chart | 0 | None exist |

## 4. Target visual language

From `design/reference/mobile-app-board.png`, a light mobile app board. Colors were
sampled from the image; sizes are estimates.

| Trait | Observed |
|---|---|
| Palette | White canvas, `#f0f0f0` tiles, near-black ink `#181617`, one ember accent `#cc3f02` |
| Accent use | Primary button, active tab, and the single highlighted bar; gray everything else |
| Secondary color | Coin amber `#f3b204` for rewards, green `#34c759` for progress |
| Inverse | Near-black tiles `#181617` for feature cards |
| Depth | Tone only: gray tiles on white, almost no shadows or borders |
| Shape | Large rounded cards, full pills for buttons and segments, sheets from the bottom |
| Hierarchy | Number-first: huge bold values (`12:30`, `100%`, `10`) above small muted labels |
| Type | Heavy, tight headings; small muted subtitles; generous white space |
| Lists | Plain grouped rows with chevrons, no dividers between groups |
| Illustration | Isometric 3D clay objects, bleeding off the corner of hero tiles |
| Charts | Gray rounded bars with one accent bar; a gray heatmap with accent cells |

### Conflicts with Saklolo

1. **Mobile vs. ops screen.** The reference is a touch app with roomy cards. The dashboard
   needs density at 1920×1080 to show many cases at once.
2. **One accent vs. priority colors.** Priority must stay readable at a glance, so status
   colors are a separate palette, exempt from the one-accent rule.
3. **Ember vs. P1 red.** They're close in hue. A P1 badge and an accent button side by side
   could read as the same thing. The proposal keeps P1 a colder crimson; verify this on screen.
4. **Light vs. video.** The reference is light; the dashboard and its screenshots are dark.
5. **Brand.** The reference is another product's design. We follow its visual language
   only: no copying its name, mascot, or illustrations.

## 5. Proposed tokens

Implemented in `design/tokens/tokens.json`.

| Group | Tokens |
|---|---|
| Color, surfaces | `canvas`, `surface`, `inverse` |
| Color, text | `ink`, `ink-muted`, `ink-faint`, `ink-on-inverse`, `ink-on-accent`, `ink-on-fill`, `ink-on-status` |
| Color, intent | `accent`, `accent-tint`, `reward`, `growth` |
| Color, status (added) | `status-critical`, `status-high`, `status-moderate`, `status-info` |
| Type | `display`, `title-l`, `title-m`, `body-bold`, `body`, `caption` |
| Radius | `sheet`, `card`, `tile`, `pill` |
| Spacing | 4pt scale: 0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64 |
| Elevation | `none`, plus `sheet` for the only surface that floats |

## 6. Components, ranked by use

| Rank | Component | Replaces | Instances |
|---|---|---|---|
| 1 | `Button` | 7 variants | 8 |
| 2 | `Input` / `Select` | 4 variants | 6 |
| 3 | `Badge` (status, count) | `PriorityBadge`, `CaseBadges`, feed labels | 4 call sites, shown on every row |
| 4 | `Card` / `Tile` | `Panel`, `Fact`, source item | 4 kinds |
| 5 | `ListRow` | Queue, feed, source rows | 3 kinds |
| 6 | `StatCard` | `StatsBar`, `Fact` | 8 |
| 7 | `Tabs` | `LaneTab` | 2 |
| 8 | `Bubble` | Phone messages | 1 kind |
| 9 | `MapPin` | Inline map styles | 2 states |
