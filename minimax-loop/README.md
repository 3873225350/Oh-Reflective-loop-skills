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
mmx skills link $(pwd)/minimax-loop
```

### 2. Initialize Loop
```bash
node minimax-loop/scripts/init_minimax_loop.cjs <LOOP_NAME>
```

### 3. Start Daemon
```bash
bash minimax-loop/scripts/start_minimax_loop.sh <LOOP_NAME>
```

## Daemon Management

| Command | Script | Purpose |
|---------|--------|---------|
| Start | `bash minimax-loop/scripts/start_minimax_loop.sh <LOOP_NAME>` | Start in tmux/nohup |
| Stop | `bash minimax-loop/scripts/stop_minimax_loop.sh <LOOP_NAME>` | Graceful stop (SIGTERM → SIGKILL) |
| Status | `bash minimax-loop/scripts/status_minimax_loop.sh <LOOP_NAME>` | Check PID health + last mode |
| Cron | `bash minimax-loop/scripts/print_cron_entry.sh` | Print cron entries for supervision |

### Cron Health Check

MiniMax-loop uses a **5-minute** health check interval (lightweight agent, fast patrol):

```bash
bash minimax-loop/scripts/print_cron_entry.sh | crontab -
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
| `MINIMAX_LOOP_WORKSPACE` | `$PWD` | Working directory |
| `MINIMAX_LOOP_STATE_DIR` | `.minimax-loop/state` | State directory |
| `MINIMAX_LOOP_LOOP_NAME` | `OPTIMIZE_ROADMAP` | Loop instance name |
| `MINIMAX_LOOP_INTERVAL` | `60` | Tick interval (seconds) |
| `MINIMAX_LOOP_LAUNCHER` | `auto` | `tmux`, `nohup`, or `auto` |

*Built by the AgentHUD Team using MiniMax-Reflective-Loop.*
