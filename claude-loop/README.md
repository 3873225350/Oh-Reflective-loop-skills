# Claude Loop Skill: Reflective ML Edition

![AgentHUD Banner](https://raw.githubusercontent.com/Harzva/agent-hud/main/media/agenthud.svg)

An autonomous, self-evolving orchestration loop powered by Claude Code. This repository implements a **Reflective Loop Architecture**, transforming Claude into a high-order software engineer capable of long-term planning and iterative self-correction.

---

## Architecture Overview

The loop treats task completion as an **iterative optimization problem**:
1. **Forward Pass (Optimize)**: Uses a Fast Adapter (`active_task.json`) for immediate implementation.
2. **Backward Signal (Check)**: Computes the "loss" and generates **Local Patches** instead of simple pass/fail.
3. **Memory Bank**: Prevents "catastrophic forgetting" of errors via `failure_bank.json`.

## Quick Start

### 1. Link the Skill
```bash
claude skills link $(pwd)/claude-loop
```

### 2. Initialize Loop
```bash
node claude-loop/scripts/init_claude_loop.cjs <LOOP_NAME>
```

### 3. Start Daemon
```bash
bash claude-loop/scripts/start_claude_loop.sh <LOOP_NAME>
```

## Daemon Management

| Command | Script | Purpose |
|---------|--------|---------|
| Start | `bash claude-loop/scripts/start_claude_loop.sh <LOOP_NAME>` | Start in tmux/nohup |
| Stop | `bash claude-loop/scripts/stop_claude_loop.sh <LOOP_NAME>` | Graceful stop (SIGTERM → SIGKILL) |
| Status | `bash claude-loop/scripts/status_claude_loop.sh <LOOP_NAME>` | Check PID health + last mode |
| Cron | `bash claude-loop/scripts/print_cron_entry.sh` | Print cron entries for supervision |

### Cron Health Check

Claude-loop uses a **10-minute** health check interval (production-grade, stable priority):

```bash
bash claude-loop/scripts/print_cron_entry.sh | crontab -
```

## State Files

| File | Metaphor | Purpose |
|------|----------|---------|
| `<LOOP_NAME>.md` | Pretrained Backbone | Global roadmap, slow-moving |
| `active_task.json` | PEFT/LoRA Adapter | Fast execution state with local patches |
| `failure_bank.json` | Failure Memory | Registry of past errors |
| `last_mode.txt` | Mode State | Tracks optimize/check alternation |

## Multi-Model Fallback

The dispatcher tries models in order until one succeeds:
1. `claude-sonnet-4-20250514`
2. `claude-haiku-4-20250514`

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLAUDE_LOOP_WORKSPACE` | `$PWD` | Working directory |
| `CLAUDE_LOOP_STATE_DIR` | `.claude-loop/state` | State directory |
| `CLAUDE_LOOP_LOOP_NAME` | `OPTIMIZE_ROADMAP` | Loop instance name |
| `CLAUDE_LOOP_INTERVAL` | `60` | Tick interval (seconds) |
| `CLAUDE_LOOP_LAUNCHER` | `auto` | `tmux`, `nohup`, or `auto` |

*Built by the AgentHUD Team using Claude-Reflective-Loop.*
