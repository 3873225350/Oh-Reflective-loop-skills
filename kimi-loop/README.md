# Kimi Loop Skill: Reflective ML Edition

![AgentHUD Banner](https://raw.githubusercontent.com/Harzva/agent-hud/main/media/agenthud.svg)

An autonomous, self-evolving orchestration loop powered by Kimi CLI. This repository implements a **Reflective Loop Architecture**, transforming Kimi into a high-order software engineer capable of long-term planning and iterative self-correction.

---

## Architecture Overview

The loop treats task completion as an **iterative optimization problem**:
1. **Forward Pass (Optimize)**: Uses a Fast Adapter (`active_task.json`) for immediate implementation.
2. **Backward Signal (Check)**: Computes the "loss" and generates **Local Patches** instead of simple pass/fail.
3. **Memory Bank**: Prevents "catastrophic forgetting" of errors via `failure_bank.json`.

## Quick Start

### 1. Link the Skill
```bash
# Link kimi-loop to your Kimi CLI
ln -s $(pwd)/kimi-loop ~/.claude/skills/kimi-loop
```

### 2. Initialize Loop
```bash
node kimi-loop/scripts/init_kimi_loop.cjs <LOOP_NAME>
```

### 3. Run Daemon
```bash
bash kimi-loop/scripts/run_daemon.sh <LOOP_NAME>
```

## State Files

| File | Purpose |
|------|---------|
| `roadmap.md` | Global plan (Pretrained Backbone) |
| `active_task.json` | Local execution state (Fast Adapter) |
| `failure_bank.json` | Error history (Reusable Memory) |
| `last_mode.txt` | Current mode (optimize/check) |

*Built with ❤️ by the AgentHUD Team using Kimi-Reflective-Loop.*