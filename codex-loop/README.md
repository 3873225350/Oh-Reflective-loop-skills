# Codex Loop Skill: Reflective ML Edition

![AgentHUD Banner](https://raw.githubusercontent.com/Harzva/agent-hud/main/media/agenthud.svg)

An autonomous, self-evolving orchestration loop powered by the Codex CLI. This repository implements a **Reflective Loop Architecture**, transforming Codex into a high-order software engineer capable of long-term planning and iterative self-correction.

---

## Architecture Overview

The loop treats task completion as an **iterative optimization problem**:
1. **Forward Pass (Optimize)**: Uses a Fast Adapter (`active_task.json`) for immediate implementation.
2. **Backward Signal (Check)**: Computes the "loss" and generates **Local Patches** instead of simple pass/fail.
3. **Memory Bank**: Prevents "catastrophic forgetting" of errors via `failure_bank.json`.

## Quick Start

### 1. Link the Skill
```bash
codex skills link $(pwd)/codex-loop
```

### 2. Initialize Loop
```bash
node codex-loop/scripts/init_codex_loop.cjs <LOOP_NAME>
```

### 3. Start Daemon
```bash
bash codex-loop/scripts/start_codex_loop.sh <LOOP_NAME>
```

## Daemon Management

| Command | Script | Purpose |
|---------|--------|---------|
| Start | `bash codex-loop/scripts/start_codex_loop.sh <LOOP_NAME>` | Start in tmux/nohup |
| Stop | `bash codex-loop/scripts/stop_codex_loop.sh <LOOP_NAME>` | Graceful stop (SIGTERM → SIGKILL) |
| Status | `bash codex-loop/scripts/status_codex_loop.sh <LOOP_NAME>` | Check PID health + last mode |
| Monitor | `bash codex-loop/scripts/monitor_codex_loop.sh [--watch]` | Real-time dashboard |
| Cron | `bash codex-loop/scripts/print_cron_entry.sh` | Print cron entries for supervision |

### Monitor Mode

The monitor provides a real-time dashboard showing daemon status, active task, failure bank, and recent logs:

```bash
# One-time snapshot
bash codex-loop/scripts/monitor_codex_loop.sh

# Continuous watch (refresh every 5s)
bash codex-loop/scripts/monitor_codex_loop.sh --watch
```

### Cron Health Check

Codex-loop uses a **10-minute** health check interval (production-stable, balanced):

```bash
bash codex-loop/scripts/print_cron_entry.sh | crontab -
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
1. `o3`
2. `o4-mini`
3. `gpt-4.1`
4. `gpt-4.1-mini`
5. `gpt-4.1-nano`

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CODEX_LOOP_WORKSPACE` | `$PWD` | Working directory |
| `CODEX_LOOP_STATE_DIR` | `.codex-loop/state` | State directory |
| `CODEX_LOOP_LOOP_NAME` | `OPTIMIZE_ROADMAP` | Loop instance name |
| `CODEX_LOOP_INTERVAL` | `60` | Tick interval (seconds) |
| `CODEX_LOOP_LAUNCHER` | `auto` | `tmux`, `nohup`, or `auto` |

*Built by the AgentHUD Team using Codex-Reflective-Loop.*
