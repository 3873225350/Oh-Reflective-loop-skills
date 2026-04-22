# MOA Loop v2.0 (Mixture of Agents)

![AgentHUD Banner](https://raw.githubusercontent.com/Harzva/agent-hud/main/media/agenthud.svg)

An intelligent orchestration loop built on **ML training paradigm**: Roadmap as pretrained weights (frozen), experiments as PEFT/Adapter fine-tuning, DAG as computation graph.

---

## Architecture

```
纵向迭代 (Epoch)                    横向DAG (Computation Graph)
─────────────────                   ─────────────────────────────
Epoch N:                            Layer 0: [research]        ← PARALLEL
  optimize ──→ check                Layer 1: [code]            ← SERIAL
     ↓            ↓                 Layer 2: [test, doc]       ← PARALLEL
  snapshot    PEFT adapt            Layer 3: [review]          ← SERIAL
     ↓            ↓
  next epoch ←──┘                   通信: Shared Blackboard
```

## Core Design: ML Training Paradigm

| ML Concept | MOA Loop Equivalent |
|---|---|
| Pretrained Weights | Roadmap backbone (frozen) |
| PEFT / LoRA | Sub-task adapter fine-tuning |
| Training Loop | optimize ↔ check epochs |
| Computation Graph | DAG task scheduling |
| Checkpoint | Iteration snapshot |

## Quick Start

```bash
# Initialize
node moa-loop/scripts/init_moa_loop.cjs <LOOP_NAME>

# Start daemon
bash moa-loop/scripts/start_moa_loop.sh <LOOP_NAME>
```

## Daemon Management

| Command | Script | Purpose |
|---------|--------|---------|
| Start | `bash moa-loop/scripts/start_moa_loop.sh <LOOP_NAME>` | Start in tmux/nohup |
| Stop | `bash moa-loop/scripts/stop_moa_loop.sh <LOOP_NAME>` | Graceful stop (SIGTERM → SIGKILL) |
| Status | `bash moa-loop/scripts/status_moa_loop.sh <LOOP_NAME>` | PID + Blackboard + mode |
| Monitor | `bash moa-loop/scripts/monitor_moa_loop.sh [--watch]` | DAG + Blackboard + PEFT dashboard |
| Cron | `bash moa-loop/scripts/print_cron_entry.sh` | Print cron entries for supervision |

### Monitor Mode

The MOA monitor provides a specialized dashboard showing DAG execution plan, Blackboard state, iteration progress, and active task:

```bash
# One-time snapshot
bash moa-loop/scripts/monitor_moa_loop.sh

# Continuous watch (refresh every 5s)
bash moa-loop/scripts/monitor_moa_loop.sh --watch
```

### Cron Health Check

MOA-loop uses a **5-minute** health check interval (multi-agent orchestration, frequent checks):

```bash
bash moa-loop/scripts/print_cron_entry.sh | crontab -
```

## Modules

| Module | Purpose |
|--------|---------|
| `core/dag_scheduler.py` | DAG scheduling with topological sort |
| `core/shared_blackboard.py` | Centralized agent communication |
| `core/iteration_manager.py` | Epoch management + PEFT adaptation |
| `run_daemon.py` | Main loop orchestrator |

## DAG Example

```
research ──→ code ──┬──→ test  ──┬──→ review
                    └──→ doc   ──┘
```

## Communication Layers

- **Horizontal** (real-time): Shared Blackboard — O(1) channels for N agents
- **Vertical** (persistent): JSON + SQLite — versioned, auditable, recoverable

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MOA_LOOP_WORKSPACE` | `$PWD` | Working directory |
| `MOA_LOOP_STATE_DIR` | `.moa-loop/state` | State directory |
| `MOA_LOOP_LOOP_NAME` | `OPTIMIZE_ROADMAP` | Loop instance name |
| `MOA_LOOP_INTERVAL` | `60` | Tick interval (seconds) |
| `MOA_LOOP_LAUNCHER` | `auto` | `tmux`, `nohup`, or `auto` |

*Built by the AgentHUD Team using MoA Architecture v2.0*
