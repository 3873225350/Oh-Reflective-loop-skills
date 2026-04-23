---
name: oh-my-icon
description: Animate iconfont-style SVG assets into polished SVG or HTML previews using local presets. Use when a user asks to make SVG icons move, create icon animation assets, or prototype a local svganimate-style workflow.
---

# Oh My Icon

Turn static SVG icons into refined animated assets.

## Workflow

1. Ask for or locate an SVG source.
2. Choose the motion intent:
   - `draw` for path reveal.
   - `pulse` for status or attention.
   - `orbit` for loop/process/system icons.
   - `float` for hero and presentation use.
3. Run the CLI:

   ```bash
   node bin/oh-my-icon.cjs input.svg --preset draw --out output.html --html
   ```

4. Open the HTML preview and inspect size, contrast, and timing.
5. Adjust `--duration`, `--color`, and `--size` until the icon feels intentional.

## Quality Bar

- Motion should communicate state or meaning, not just decorate.
- Keep animation under 2.4 seconds unless it is a background loop.
- Preserve the original icon geometry.
- Prefer CSS animation over JavaScript for embeddable assets.

