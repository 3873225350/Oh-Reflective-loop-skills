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
kimi skills link $(pwd)/kimi-loop
```

### 2. Initialize Loop
```bash
node kimi-loop/scripts/init_kimi_loop.cjs <LOOP_NAME>
```

### 3. Start Daemon
```bash
bash kimi-loop/scripts/start_kimi_loop.sh <LOOP_NAME>
```

## Daemon Management

| Command | Script | Purpose |
|---------|--------|---------|
| Start | `bash kimi-loop/scripts/start_kimi_loop.sh <LOOP_NAME>` | Start in tmux/nohup |
| Stop | `bash kimi-loop/scripts/stop_kimi_loop.sh <LOOP_NAME>` | Graceful stop (SIGTERM → SIGKILL) |
| Status | `bash kimi-loop/scripts/status_kimi_loop.sh <LOOP_NAME>` | Check PID health + last mode |
| Cron | `bash kimi-loop/scripts/print_cron_entry.sh` | Print cron entries for supervision |

### Cron Health Check

Kimi-loop uses a **15-minute** health check interval (long-context tasks, wider interval):

```bash
bash kimi-loop/scripts/print_cron_entry.sh | crontab -
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
| `KIMI_LOOP_WORKSPACE` | `$PWD` | Working directory |
| `KIMI_LOOP_STATE_DIR` | `.kimi-loop/state` | State directory |
| `KIMI_LOOP_LOOP_NAME` | `OPTIMIZE_ROADMAP` | Loop instance name |
| `KIMI_LOOP_INTERVAL` | `60` | Tick interval (seconds) |
| `KIMI_LOOP_LAUNCHER` | `auto` | `tmux`, `nohup`, or `auto` |

*Built by the AgentHUD Team using Kimi-Reflective-Loop.*
