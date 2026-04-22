# Cursor Loop Skill: Reflective ML Edition

![AgentHUD Banner](https://raw.githubusercontent.com/Harzva/agent-hud/main/media/agenthud.svg)

An autonomous, self-evolving orchestration loop powered by Cursor. This repository implements a **Reflective Loop Architecture**, transforming Cursor into a high-order software engineer capable of long-term planning and iterative self-correction.

---

## Architecture Overview

The loop treats task completion as an **iterative optimization problem**:
1. **Forward Pass (Optimize)**: Uses a Fast Adapter (`active_task.json`) for immediate implementation.
2. **Backward Signal (Check)**: Computes the "loss" and generates **Local Patches** instead of simple pass/fail.
3. **Memory Bank**: Prevents "catastrophic forgetting" of errors via `failure_bank.json`.

## Quick Start

### 1. Link the Skill
```bash
ln -s $(pwd)/cursor-loop ~/.cursor/skills/cursor-loop
```

### 2. Initialize Loop
```bash
node cursor-loop/scripts/init_cursor_loop.cjs <LOOP_NAME>
```

### 3. Start Daemon
```bash
bash cursor-loop/scripts/start_cursor_loop.sh <LOOP_NAME>
```

## Daemon Management

| Command | Script | Purpose |
|---------|--------|---------|
| Start | `bash cursor-loop/scripts/start_cursor_loop.sh <LOOP_NAME>` | Start in tmux/nohup |
| Stop | `bash cursor-loop/scripts/stop_cursor_loop.sh <LOOP_NAME>` | Graceful stop (SIGTERM → SIGKILL) |
| Status | `bash cursor-loop/scripts/status_cursor_loop.sh <LOOP_NAME>` | Check PID health + last mode |
| Cron | `bash cursor-loop/scripts/print_cron_entry.sh` | Print cron entries for supervision |

### Cron Health Check

Cursor-loop uses a **15-minute** health check interval (IDE integration, less frequent):

```bash
bash cursor-loop/scripts/print_cron_entry.sh | crontab -
```

## State Files

| File | Metaphor | Purpose |
|------|----------|---------|
| `<LOOP_NAME>.md` | Pretrained Backbone | Global roadmap, slow-moving |
| `active_task.json` | PEFT/LoRA Adapter | Fast execution state with local patches |
| `failure_bank.json` | Failure Memory | Registry of past errors |
| `last_mode.txt` | Mode State | Tracks optimize/check alternation |

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CURSOR_LOOP_WORKSPACE` | `$PWD` | Working directory |
| `CURSOR_LOOP_STATE_DIR` | `.cursor-loop/state` | State directory |
| `CURSOR_LOOP_LOOP_NAME` | `OPTIMIZE_ROADMAP` | Loop instance name |
| `CURSOR_LOOP_INTERVAL` | `60` | Tick interval (seconds) |
| `CURSOR_LOOP_LAUNCHER` | `auto` | `tmux`, `nohup`, or `auto` |

*Built by the AgentHUD Team using Cursor-Reflective-Loop.*
