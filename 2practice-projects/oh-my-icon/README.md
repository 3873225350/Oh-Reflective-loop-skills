# Oh My Icon

A small SVG animation CLI and skill prototype inspired by `svganimate.ai` and iconfont-style workflows.

This first version is local and dependency-free. It does not call a remote SVG animation service. It wraps an input SVG with CSS animation presets and can emit either animated SVG or an HTML preview.

## Usage

```bash
node bin/oh-my-icon.cjs examples/loop.svg --preset draw --out examples/loop.draw.html --html
node bin/oh-my-icon.cjs examples/loop.svg --preset pulse --out examples/loop.pulse.svg
```

## Presets

- `draw` — animated stroke drawing for line icons.
- `pulse` — breathing scale and glow.
- `orbit` — slow rotation with hover acceleration.
- `float` — gentle presentation motion for landing pages.

## Skill Direction

`SKILL.md` describes how this can become a Codex skill: feed an iconfont SVG, pick motion intent, generate preview assets, inspect, and refine.

