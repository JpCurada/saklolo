// Generates CSS variables, a typed TS object, and the Tailwind theme from
// design/tokens/tokens.json, and fails if a text/background pair is below WCAG AA.
// Run with `npm run tokens` (or `make tokens` from the repo root).
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";

const SOURCE = "../design/tokens/tokens.json";
const OUT_DIR = "lib/tokens";
const BANNER = "Generated from design/tokens/tokens.json by `make tokens`. Do not edit.";
const WCAG_AA_TEXT = 4.5;

// tokens.json is validated by use: a missing path throws in lookup().
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Node = Record<string, any>;
const root: Node = JSON.parse(readFileSync(SOURCE, "utf-8"));

/** Every text color and the backgrounds it may sit on. AA applies in both themes. */
const CONTRAST_PAIRS: [text: string, backgrounds: string[]][] = [
  ["ink", ["canvas", "surface", "accent-tint"]],
  ["ink-on-fill", ["reward", "growth"]],
  ["ink-muted", ["canvas", "surface", "accent-tint"]],
  ["ink-faint", ["canvas", "surface", "accent-tint"]],
  ["ink-on-inverse", ["inverse"]],
  ["ink-on-accent", ["accent"]],
  ["ink-on-status", ["status-critical", "status-high", "status-moderate", "status-info"]],
  ["accent", ["canvas", "accent-tint"]],
];

function lookup(path: string): Node {
  return path.split(".").reduce((node, key) => {
    if (!(key in node)) throw new Error(`Unknown token reference: ${path}`);
    return node[key];
  }, root);
}

/** Follow {alias} references down to a raw value. */
function resolve(value: unknown): unknown {
  const alias = typeof value === "string" && value.match(/^\{(.+)\}$/);
  return alias ? resolve(lookup(alias[1]).$value) : value;
}

const px = (d: { value: number; unit: string }) => `${d.value}${d.unit}`;
const fontStack = (family: unknown) =>
  (resolve(family) as string[]).map((f) => (f.includes(" ") ? `"${f}"` : f)).join(", ");

function color(name: string, theme: "light" | "dark"): string {
  const token = root.semantic.color[name];
  const dark = token.$extensions?.saklolo?.dark;
  return resolve(theme === "dark" ? dark : token.$value) as string;
}

function luminance(hex: string): number {
  const channels = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const [r, g, b] = channels.map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

function checkContrast(): void {
  const failures: string[] = [];
  let lowest = Infinity;
  for (const theme of ["light", "dark"] as const) {
    for (const [text, backgrounds] of CONTRAST_PAIRS) {
      for (const background of backgrounds) {
        const ratio = contrast(color(text, theme), color(background, theme));
        lowest = Math.min(lowest, ratio);
        if (ratio < WCAG_AA_TEXT) {
          failures.push(`${theme}: ${text} on ${background} is ${ratio.toFixed(2)}:1`);
        }
      }
    }
  }
  if (failures.length > 0) {
    console.error(`Contrast below WCAG AA (${WCAG_AA_TEXT}:1):\n  ${failures.join("\n  ")}`);
    process.exit(1);
  }
  const pairs = CONTRAST_PAIRS.reduce((sum, [, backgrounds]) => sum + backgrounds.length, 0);
  console.log(`Contrast OK: ${pairs * 2} pairs, lowest ${lowest.toFixed(2)}:1`);
}

function shadow(name: string): string {
  const { offsetX, offsetY, blur, spread, color: shade } = root.semantic.elevation[name].$value;
  return name === "none"
    ? "none"
    : `${px(offsetX)} ${px(offsetY)} ${px(blur)} ${px(spread)} ${shade}`;
}

/** A CSS duration or timing function. */
function motion(name: string): string {
  const value = root.semantic.motion[name].$value;
  return Array.isArray(value) ? `cubic-bezier(${value.join(", ")})` : px(value);
}

interface TextStyle {
  family: string;
  weight: number;
  size: string;
  lineHeight: number;
  tracking: string;
}

function textStyle(name: string): TextStyle {
  const value = root.semantic.typography[name].$value;
  return {
    family: fontStack(value.fontFamily),
    weight: resolve(value.fontWeight) as number,
    size: px(value.fontSize),
    lineHeight: value.lineHeight,
    tracking: px(value.letterSpacing),
  };
}

const names = (group: Node) => Object.keys(group).filter((key) => !key.startsWith("$"));
const colors = names(root.semantic.color);
const componentColors = names(root.component.color);
const spaces = names(root.primitive.space);
const radii = names(root.semantic.radius);
const strokes = names(root.semantic.stroke);
const texts = names(root.semantic.typography);
const elevations = names(root.semantic.elevation);
const motions = names(root.semantic.motion);

/** Component tokens alias semantic ones, so they follow the theme through var(). */
const componentVar = (name: string) => {
  const alias = root.component.color[name].$value.match(/^\{semantic\.color\.(.+)\}$/);
  return alias ? `var(--sk-color-${alias[1]})` : resolve(root.component.color[name].$value);
};

function css(): string {
  const themed = (theme: "light" | "dark") =>
    colors.map((name) => `  --sk-color-${name}: ${color(name, theme)};`).join("\n");
  const lines = [
    ...componentColors.map((name) => `  --sk-color-${name}: ${componentVar(name)};`),
    ...spaces.map((key) => `  --sk-space-${key}: ${px(root.primitive.space[key].$value)};`),
    ...radii.map((key) => `  --sk-radius-${key}: ${px(root.semantic.radius[key].$value)};`),
    ...strokes.map((key) => `  --sk-stroke-${key}: ${px(root.semantic.stroke[key].$value)};`),
    ...elevations.map((key) => `  --sk-elevation-${key}: ${shadow(key)};`),
    ...motions.map((key) => `  --sk-motion-${key}: ${motion(key)};`),
    ...texts.flatMap((key) => {
      const t = textStyle(key);
      return [
        `  --sk-text-${key}-family: ${t.family};`,
        `  --sk-text-${key}-weight: ${t.weight};`,
        `  --sk-text-${key}-size: ${t.size};`,
        `  --sk-text-${key}-line-height: ${t.lineHeight};`,
        `  --sk-text-${key}-tracking: ${t.tracking};`,
      ];
    }),
  ];
  return `/* ${BANNER} */
:root {
${themed("light")}
${lines.join("\n")}
}

[data-theme="dark"] {
${themed("dark")}
}
`;
}

function tailwindTheme(): string {
  const lines = [
    "  --*: initial; /* replace Tailwind's defaults: only our tokens exist */",
    ...[...colors, ...componentColors].map((n) => `  --color-${n}: var(--sk-color-${n});`),
    ...spaces.map((key) => `  --spacing-${key}: var(--sk-space-${key});`),
    ...radii.map((key) => `  --radius-${key}: var(--sk-radius-${key});`),
    ...elevations.map((key) => `  --shadow-${key}: var(--sk-elevation-${key});`),
    ...texts.flatMap((key) => [
      `  --text-${key}: var(--sk-text-${key}-size);`,
      `  --text-${key}--line-height: var(--sk-text-${key}-line-height);`,
      `  --text-${key}--font-weight: var(--sk-text-${key}-weight);`,
      `  --text-${key}--letter-spacing: var(--sk-text-${key}-tracking);`,
    ]),
    `  --font-sans: ${fontStack(root.primitive.font.family.sans.$value)};`,
    `  --font-mono: ${fontStack(root.primitive.font.family.mono.$value)};`,
  ];
  return `/* ${BANNER} */\n@theme inline {\n${lines.join("\n")}\n}\n`;
}

function typescript(): string {
  const entries = (keys: string[], prefix: string) =>
    Object.fromEntries(keys.map((key) => [key, `var(--sk-${prefix}-${key})`]));
  const tokens = {
    color: entries([...colors, ...componentColors], "color"),
    space: entries(spaces, "space"),
    radius: entries(radii, "radius"),
    stroke: entries(strokes, "stroke"),
    elevation: entries(elevations, "elevation"),
    motion: entries(motions, "motion"),
    text: Object.fromEntries(texts.map((key) => [key, textStyle(key)])),
    theme: {
      light: Object.fromEntries(colors.map((name) => [name, color(name, "light")])),
      dark: Object.fromEntries(colors.map((name) => [name, color(name, "dark")])),
    },
  };
  return `// ${BANNER}
export const tokens = ${JSON.stringify(tokens, null, 2)} as const;

export type ColorToken = keyof typeof tokens.color;
export type SpaceToken = keyof typeof tokens.space;
export type RadiusToken = keyof typeof tokens.radius;
export type TextToken = keyof typeof tokens.text;
`;
}

checkContrast();
mkdirSync(OUT_DIR, { recursive: true });
writeFileSync(`${OUT_DIR}/tokens.css`, css());
writeFileSync(`${OUT_DIR}/tailwind-theme.css`, tailwindTheme());
writeFileSync(`${OUT_DIR}/tokens.ts`, typescript());
console.log(`Wrote ${OUT_DIR}/tokens.css, tailwind-theme.css, tokens.ts`);
