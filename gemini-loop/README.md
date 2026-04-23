# Gemini Loop Skill: Reflective ML Edition

![AgentHUD Banner](https://raw.githubusercontent.com/Harzva/agent-hud/main/media/agenthud.svg)

An autonomous, self-evolving orchestration loop powered by Gemini CLI. This repository implements a **Reflective Loop Architecture**, transforming Gemini into a high-order software engineer capable of long-term planning and iterative self-correction.

---

## Architecture Overview

The loop treats task completion as an **iterative optimization problem**:
1. **Forward Pass (Optimize)**: Uses a Fast Adapter (`active_task.json`) for immediate implementation.
2. **Backward Signal (Check)**: Computes the "loss" and generates **Local Patches** instead of simple pass/fail.
3. **Memory Bank**: Prevents "catastrophic forgetting" of errors via `failure_bank.json`.

## Quick Start

### 1. Link the Skill
```bash
gemini skills link $(pwd)/gemini-loop
```

### 2. Initialize Loop
```bash
node gemini-loop/scripts/init_gemini_loop.cjs <LOOP_NAME>
```

### 3. Start Daemon
```bash
bash gemini-loop/scripts/start_daemon.sh <LOOP_NAME>
```

## Daemon Management

| Command | Script | Purpose |
|---------|--------|---------|
| Start | `bash gemini-loop/scripts/start_daemon.sh <LOOP_NAME>` | Start in tmux/nohup |
| Stop | `bash gemini-loop/scripts/stop_daemon.sh <LOOP_NAME>` | Graceful stop (SIGTERM → SIGKILL) |
| Status | `bash gemini-loop/scripts/status_daemon.sh <LOOP_NAME>` | Check PID health + last mode |
| Cron | `bash gemini-loop/scripts/print_cron_entry.sh` | Print cron entries for supervision |

### Cron Health Check

Gemini-loop uses a **5-minute** health check interval (fast iteration, reference agent):

```bash
bash gemini-loop/scripts/print_cron_entry.sh | crontab -
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
| `GEMINI_LOOP_WORKSPACE` | `$PWD` | Working directory |
| `GEMINI_LOOP_STATE_DIR` | `.reflective-loop/state` | State directory |
| `GEMINI_LOOP_LOOP_NAME` | `OPTIMIZE_ROADMAP` | Loop instance name |
| `GEMINI_LOOP_INTERVAL` | `60` | Tick interval (seconds) |
| `GEMINI_LOOP_LAUNCHER` | `auto` | `tmux`, `nohup`, or `auto` |

*Built by the AgentHUD Team using Gemini-Reflective-Loop.*
