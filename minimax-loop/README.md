# MiniMax Loop Skill: Reflective ML Edition

![AgentHUD Banner](https://raw.githubusercontent.com/Harzva/agent-hud/main/media/agenthud.svg)

An autonomous, self-evolving orchestration loop powered by MiniMax CLI (mmx). This repository implements a **Reflective Loop Architecture**, transforming MiniMax into a high-order software engineer capable of long-term planning and iterative self-correction.

---

## Architecture Overview

The loop treats task completion as an **iterative optimization problem**:
1. **Forward Pass (Optimize)**: Uses a Fast Adapter (`active_task.json`) for immediate implementation.
2. **Backward Signal (Check)**: Computes the "loss" and generates **Local Patches** instead of simple pass/fail.
3. **Memory Bank**: Prevents "catastrophic forgetting" of errors via `failure_bank.json`.

## Quick Start

### 1. Link the Skill
```bash
# Link minimax-loop to your MiniMax CLI
ln -s $(pwd)/minimax-loop ~/.claude/skills/minimax-loop
```

### 2. Initialize Loop
```bash
node minimax-loop/scripts/init_minimax_loop.cjs <LOOP_NAME>
```

### 3. Run Daemon
```bash
bash minimax-loop/scripts/run_daemon.sh <LOOP_NAME>
```

## State Files

| File | Purpose |
|------|---------|
| `roadmap.md` | Global plan (Pretrained Backbone) |
| `active_task.json` | Local execution state (Fast Adapter) |
| `failure_bank.json` | Error history (Reusable Memory) |
| `last_mode.txt` | Current mode (optimize/check) |

*Built with ❤️ by the AgentHUD Team using MiniMax-Reflective-Loop.*