// Renders design/assets/*.svg to web/public/assets. Run with `npm run assets`.
// Sources use {{name}} placeholders, filled from PALETTE: the one place colors live.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import sharp from "sharp";

const SOURCE = "../design/assets";
const OUT = "public/assets";
const SCENES = [
  "scene-queue-clear",
  "scene-review-clear",
  "scene-no-selection",
  "scene-api-down",
  "scene-boot",
];
const SCENE_LIMIT = 60_000;
const ANIMATED_LIMIT = 400_000;
const FRAMES = 24;
const FRAME_MS = 83;

const tokens = JSON.parse(readFileSync("../design/tokens/tokens.json", "utf-8"));
const darkToken = (name) => {
  const token = tokens.semantic.color[name];
  const value = token.$extensions?.saklolo?.dark ?? token.$value;
  const alias = value.match(/^\{(.+)\}$/);
  return alias ? alias[1].split(".").reduce((node, key) => node[key], tokens).$value : value;
};
const TOKENS = [
  "canvas",
  "surface",
  "ink",
  "ink-muted",
  "ink-faint",
  "ink-on-fill",
  "accent",
  "reward",
  "growth",
];

// Dark token values, plus storm and flood tints that exist only in these images.
const PALETTE = {
  ...Object.fromEntries(TOKENS.map((name) => [name, darkToken(name)])),
  critical: darkToken("status-critical"),
  stormDeep: "#141a24",
  storm: "#232b38",
  stormLight: "#3a4557",
  water: "#1f4a5e",
  waterLight: "#2f6f84",
  waterFoam: "#8fc3cf",
  earth: "#2f2a27",
  earthLight: "#463e38",
  roof: "#5a3a30",
  roofLight: "#7a5040",
  wall: "#3b3836",
  wallLight: "#57524e",
};

function fill(svg, values) {
  return svg.replace(/\{\{([\w-]+)\}\}/g, (_, key) => {
    if (!(key in values)) throw new Error(`Unknown placeholder: ${key}`);
    return values[key];
  });
}

const read = (name) => readFileSync(`${SOURCE}/${name}.svg`, "utf-8");
const minify = (svg) => svg.replace(/>\s+</g, "><").trim();

/** Seeded (mulberry32), so a rebuild gives the same rain. */
function random(seed) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const next = random(20261102);
const DROPS = Array.from({ length: 70 }, () => ({
  x: next() * 880,
  y: next() * 640,
  length: 14 + next() * 14,
  laps: 1 + Math.floor(next() * 2),
}));

/** Every drop falls a whole number of screen heights per loop, so frame 24 is frame 0. */
function bootValues(frame) {
  const phase = frame / FRAMES;
  const rain = DROPS.map((drop) => {
    const y = (drop.y + phase * drop.laps * 640) % 640;
    const x = drop.x - y * 0.14;
    const a = `${x.toFixed(1)} ${(y - 20).toFixed(1)}`;
    const b = `${(x - drop.length * 0.14).toFixed(1)} ${(y - 20 + drop.length).toFixed(1)}`;
    return `<path d="M${a}L${b}"/>`;
  }).join("");
  const pulse = 0.5 + 0.5 * Math.cos(2 * Math.PI * phase);
  return {
    rain,
    shimmer: (-phase * 60).toFixed(1),
    glowRadius: (86 + pulse * 40).toFixed(1),
    glowOpacity: (0.45 + pulse * 0.5).toFixed(2),
  };
}

/** Best quality that fits the limit, so assets stay as sharp as their budget allows. */
async function fitWebp(encode, limit) {
  for (let quality = 86; quality >= 30; quality -= 4) {
    const buffer = await encode(quality);
    if (buffer.length <= limit) return { buffer, quality };
  }
  throw new Error(`Can't fit under ${limit} bytes`);
}

async function main() {
  mkdirSync(OUT, { recursive: true });
  writeFileSync(`${OUT}/logo-mark.svg`, minify(fill(read("logo-mark"), PALETTE)));

  for (const name of SCENES) {
    const values = { ...PALETTE, ...(name === "scene-boot" ? bootValues(0) : {}) };
    const svg = Buffer.from(fill(read(name), values));
    const { buffer, quality } = await fitWebp(
      (q) => sharp(svg).webp({ quality: q, alphaQuality: 90, effort: 6 }).toBuffer(),
      SCENE_LIMIT,
    );
    writeFileSync(`${OUT}/${name}.webp`, buffer);
    console.log(`${name}.webp q${quality} ${buffer.length} bytes`);
  }

  const frames = await Promise.all(
    Array.from({ length: FRAMES }, (_, frame) =>
      sharp(Buffer.from(fill(read("scene-boot"), { ...PALETTE, ...bootValues(frame) })))
        .png()
        .toBuffer(),
    ),
  );
  const { buffer, quality } = await fitWebp(
    (q) =>
      sharp(frames, { join: { animated: true } })
        .webp({
          quality: q,
          alphaQuality: 80,
          effort: 6,
          loop: 0,
          delay: Array(FRAMES).fill(FRAME_MS),
        })
        .toBuffer(),
    ANIMATED_LIMIT,
  );
  writeFileSync(`${OUT}/scene-boot-animated.webp`, buffer);

  console.log(`scene-boot-animated.webp q${quality} ${buffer.length} bytes`);
}

await main();
