#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const args = process.argv.slice(2);

function usage() {
  console.log(`Oh My Icon

Usage:
  node bin/oh-my-icon.cjs input.svg --preset draw --out output.html --html

Options:
  --preset <draw|pulse|orbit|float>
  --out <file>
  --html
  --duration <seconds>
  --color <css-color>
  --size <px>
`);
}

function readOption(name, fallback) {
  const index = args.indexOf(name);
  if (index === -1) return fallback;
  return args[index + 1] || fallback;
}

const input = args.find((arg) => !arg.startsWith("--"));
if (!input || args.includes("--help") || args.includes("-h")) {
  usage();
  process.exit(input ? 0 : 1);
}

const preset = readOption("--preset", "draw");
const outFile = readOption("--out", "");
const duration = Number(readOption("--duration", "1.8"));
const color = readOption("--color", "#141513");
const size = Number(readOption("--size", "192"));
const emitHtml = args.includes("--html") || (outFile && outFile.endsWith(".html"));

const source = fs.readFileSync(input, "utf8");

function normalizeSvg(svg) {
  return svg
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/\s(width|height)="[^"]*"/g, "")
    .replace(/<svg\b/, `<svg class="omi-svg"`);
}

function presetCss(name) {
  const seconds = `${duration}s`;
  const base = `
.omi-wrap {
  width: ${size}px;
  height: ${size}px;
  display: inline-grid;
  place-items: center;
  color: ${color};
}
.omi-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}
.omi-svg path,
.omi-svg circle,
.omi-svg rect,
.omi-svg line,
.omi-svg polyline,
.omi-svg polygon {
  vector-effect: non-scaling-stroke;
  transform-box: fill-box;
  transform-origin: center;
}
`;

  const presets = {
    draw: `
${base}
.omi-svg path,
.omi-svg circle,
.omi-svg rect,
.omi-svg line,
.omi-svg polyline,
.omi-svg polygon {
  stroke-dasharray: 420;
  stroke-dashoffset: 420;
  animation: omi-draw ${seconds} cubic-bezier(.2,.8,.2,1) infinite alternate;
}
@keyframes omi-draw {
  to { stroke-dashoffset: 0; }
}
`,
    pulse: `
${base}
.omi-svg {
  animation: omi-pulse ${seconds} ease-in-out infinite;
  filter: drop-shadow(0 14px 22px color-mix(in srgb, ${color}, transparent 68%));
}
@keyframes omi-pulse {
  0%, 100% { transform: scale(1); opacity: .84; }
  50% { transform: scale(1.08); opacity: 1; }
}
`,
    orbit: `
${base}
.omi-svg {
  animation: omi-orbit ${seconds} linear infinite;
}
.omi-wrap:hover .omi-svg {
  animation-duration: ${Math.max(duration * 0.42, 0.5)}s;
}
@keyframes omi-orbit {
  to { transform: rotate(360deg); }
}
`,
    float: `
${base}
.omi-svg {
  animation: omi-float ${seconds} ease-in-out infinite;
  filter: drop-shadow(0 18px 24px color-mix(in srgb, ${color}, transparent 76%));
}
@keyframes omi-float {
  0%, 100% { transform: translateY(0) rotate(-1deg); }
  50% { transform: translateY(-10px) rotate(1deg); }
}
`
  };

  if (!presets[name]) {
    throw new Error(`Unknown preset: ${name}`);
  }
  return presets[name].trim();
}

const css = presetCss(preset);
const svg = normalizeSvg(source);
const animated = `<style>${css}</style>\n<span class="omi-wrap">${svg}</span>\n`;
const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Oh My Icon Preview</title>
    <style>
      body {
        min-height: 100vh;
        margin: 0;
        display: grid;
        place-items: center;
        background: #fbf8f0;
      }
      ${css}
    </style>
  </head>
  <body>
    <span class="omi-wrap">${svg}</span>
  </body>
</html>
`;

const output = emitHtml ? html : animated;

if (outFile) {
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, output);
  console.log(`Generated ${outFile}`);
} else {
  process.stdout.write(output);
}
