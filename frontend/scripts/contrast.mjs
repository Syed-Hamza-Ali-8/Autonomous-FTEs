// WCAG 2.x contrast checker for the design tokens (spec Section 13.2 / 13.6: AA in light and dark).
// Colours are Tailwind palette names read from the installed theme.css, so values are never typed by hand.
//
// Usage: node scripts/contrast.mjs '[["label", "fg", "bg", minRatio], ...]'
//   fg/bg: a palette name ("zinc-500", "white"), or "name/alpha@bgname" for a translucent colour over bgname.
// Exits 1 if any pair is below its minimum (4.5 for text, 3 for icons, borders and focus rings).
import fs from "node:fs";

const css = fs.readFileSync(new URL("../node_modules/tailwindcss/theme.css", import.meta.url), "utf8");
const pal = { white: [1, 0, 0], black: [0, 0, 0] };
for (const m of css.matchAll(/--color-([a-z]+-\d+):\s*oklch\(([\d.]+)%\s+([\d.]+|none)\s+([\d.]+|none)\)/g)) {
  pal[m[1]] = [parseFloat(m[2]) / 100, m[3] === "none" ? 0 : +m[3], m[4] === "none" ? 0 : +m[4]];
}

// oklch -> linear sRGB (Björn Ottosson's OKLab matrices), clamped to gamut.
const toLinear = ([L, C, h]) => {
  const a = C * Math.cos((h * Math.PI) / 180);
  const b = C * Math.sin((h * Math.PI) / 180);
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  return [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  ].map((v) => Math.min(1, Math.max(0, v)));
};
const encode = (v) => (v <= 0.0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - 0.055);
const decode = (v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);

const srgb = (spec) => {
  const [colour, over] = spec.split("@");
  const [name, alpha] = colour.split("/");
  if (!pal[name]) throw new Error(`unknown colour ${name}`);
  const fg = toLinear(pal[name]).map(encode);
  if (!alpha) return fg;
  const bg = srgb(over);
  const a = Number(alpha) / 100;
  return fg.map((v, i) => v * a + bg[i] * (1 - a));
};
const luminance = (spec) => {
  const [r, g, b] = srgb(spec).map(decode);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const ratio = (fg, bg) => {
  const [hi, lo] = [luminance(fg), luminance(bg)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};

let failed = 0;
for (const [label, fg, bg, min] of JSON.parse(process.argv[2] ?? "[]")) {
  const r = ratio(fg, bg);
  if (r < min) failed++;
  console.log(`${r >= min ? "PASS" : "FAIL"} ${r.toFixed(2).padStart(5)} (min ${min})  ${label}: ${fg} on ${bg}`);
}
process.exit(failed ? 1 : 0);
