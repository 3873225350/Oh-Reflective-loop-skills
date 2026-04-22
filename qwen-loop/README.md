# Qwen Loop Skill: Reflective ML Edition

![AgentHUD Banner](https://raw.githubusercontent.com/Harzva/agent-hud/main/media/agenthud.svg)

An autonomous, self-evolving orchestration loop powered by Qwen CLI. This repository implements a **Reflective Loop Architecture**, transforming Qwen into a high-order software engineer capable of long-term planning and iterative self-correction.

---

## Architecture Overview

The loop treats task completion as an **iterative optimization problem**:
1. **Forward Pass (Optimize)**: Uses a Fast Adapter (`active_task.json`) for immediate implementation.
2. **Backward Signal (Check)**: Computes the "loss" and generates **Local Patches** instead of simple pass/fail.
3. **Memory Bank**: Prevents "catastrophic forgetting" of errors via `failure_bank.json`.

## Quick Start

### 1. Link the Skill
```bash
qwen skills link $(pwd)/qwen-loop
```

### 2. Initialize Loop
```bash
node qwen-loop/scripts/init_qwen_loop.cjs <LOOP_NAME>
```

### 3. Start Daemon
```bash
bash qwen-loop/scripts/start_qwen_loop.sh <LOOP_NAME>
```

## Daemon Management

| Command | Script | Purpose |
|---------|--------|---------|
| Start | `bash qwen-loop/scripts/start_qwen_loop.sh <LOOP_NAME>` | Start in tmux/nohup |
| Stop | `bash qwen-loop/scripts/stop_qwen_loop.sh <LOOP_NAME>` | Graceful stop (SIGTERM → SIGKILL) |
| Status | `bash qwen-loop/scripts/status_qwen_loop.sh <LOOP_NAME>` | Check PID health + last mode |
| Cron | `bash qwen-loop/scripts/print_cron_entry.sh` | Print cron entries for supervision |

### Cron Health Check

Qwen-loop uses a **10-minute** health check interval (balanced strategy):

```bash
bash qwen-loop/scripts/print_cron_entry.sh | crontab -
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
| `QWEN_LOOP_WORKSPACE` | `$PWD` | Working directory |
| `QWEN_LOOP_STATE_DIR` | `.qwen-loop/state` | State directory |
| `QWEN_LOOP_LOOP_NAME` | `OPTIMIZE_ROADMAP` | Loop instance name |
| `QWEN_LOOP_INTERVAL` | `60` | Tick interval (seconds) |
| `QWEN_LOOP_LAUNCHER` | `auto` | `tmux`, `nohup`, or `auto` |

*Built by the AgentHUD Team using Qwen-Reflective-Loop.*
