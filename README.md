# Oh-Reflective-Loop-Skills

![AgentHUD Banner](https://raw.githubusercontent.com/Harzva/agent-hud/main/media/agenthud.svg)

A collection of **self-contained, autonomous Reflective Loop skills** for various AI coding agents. Each skill implements the same ML-inspired architecture but targets a different CLI.

---

## Architecture

Every skill treats long-horizon agent work as an **iterative optimization problem**:

1. **Forward Pass (optimize)**: Implementation agent reads failure history and applies local patches, then executes one bounded slice of work.
2. **Backward Signal (check)**: Checker agent reviews the result, computes the "loss", and generates **Local Patches** to guide the next pass.
3. **Failure Memory**: Prevents "catastrophic forgetting" of errors via `failure_bank.json`.

### State Files

| File | Metaphor | Purpose |
|------|----------|---------|
| `<LOOP_NAME>.md` | Pretrained Backbone | Global roadmap, slow-moving |
| `active_task.json` | PEFT/LoRA Adapter | Fast execution state with local patches |
| `failure_bank.json` | Failure Memory | Registry of past errors |
| `last_mode.txt` | Mode State | Tracks optimize/check alternation |

---

## Skills

| Skill | CLI | State Dir | Models | Health Check |
|-------|-----|-----------|--------|:------------:|
| [gemini-loop](gemini-loop/) | `gemini` | `.reflective-loop/state` | 5 models (flash/pro) | `*/5` |
| [codex-loop](codex-loop/) | `codex` | `.codex-loop/state` | 5 models (o3, o4-mini, gpt-4.1) | `*/10` |
| [claude-loop](claude-loop/) | `claude` | `.claude-loop/state` | 2 models (sonnet, haiku) | `*/10` |
| [cursor-loop](cursor-loop/) | `cursor` | `.cursor-loop/state` | default | `*/15` |
| [kimi-loop](kimi-loop/) | `kimi` | `.kimi-loop/state` | default | `*/15` |
| [minimax-loop](minimax-loop/) | `mmx` | `.minimax-loop/state` | default | `*/5` |
| [qwen-loop](qwen-loop/) | `qwen` | `.qwen-loop/state` | default | `*/10` |
| [moa-loop](moa-loop/) | multi | `.moa-loop/state` | all agents | `*/5` |

---

## Quick Start (Any Skill)

```bash
# 1. Initialize
node <skill>-loop/scripts/init_<name>_loop.cjs MY_ROADMAP

# 2. Start daemon (tmux/nohup auto-select)
bash <skill>-loop/scripts/start_<name>_loop.sh MY_ROADMAP

# 3. Check status
bash <skill>-loop/scripts/status_<name>_loop.sh MY_ROADMAP
```

### Daemon Management (All Skills)

Every skill provides the same daemon management interface:

| Command | Script | Purpose |
|---------|--------|---------|
| Start | `start_<name>_loop.sh` | Start daemon in tmux/nohup with PID tracking |
| Stop | `stop_<name>_loop.sh` | Graceful stop (SIGTERM → wait → SIGKILL) |
| Status | `status_<name>_loop.sh` | Check PID health + last mode + recent logs |
| Cron | `print_cron_entry.sh` | Print `@reboot` + health-check cron entries |

**gemini-loop** uses `start_daemon.sh` / `status_daemon.sh` naming.

### Extended Commands (Select Skills)

**codex-loop** includes additional monitoring:
```bash
bash codex-loop/scripts/monitor_codex_loop.sh          # snapshot dashboard
bash codex-loop/scripts/monitor_codex_loop.sh --watch   # continuous watch
```

**moa-loop** includes DAG + Blackboard monitoring:
```bash
bash moa-loop/scripts/monitor_moa_loop.sh               # DAG + Blackboard snapshot
bash moa-loop/scripts/monitor_moa_loop.sh --watch       # continuous watch
```

---

## Cron Integration

Every skill includes `print_cron_entry.sh` for OS-level supervision:

```bash
# Print cron entries for a single skill
bash <skill>-loop/scripts/print_cron_entry.sh

# Install all skills into crontab at once
{
  for skill in gemini codex claude cursor kimi minimax qwen moa; do
    bash ${skill}-loop/scripts/print_cron_entry.sh
  done
} | crontab -
```

Cron provides two functions:
- **`@reboot`** — Auto-start daemon after machine reboot
- **`*/N * * * *`** — Periodic health check, auto-restart on failure

See [references/cron-integration.md](references/cron-integration.md) for full documentation.

---

## Design Principles

1. **Self-Contained**: Every skill is fully independent with zero external dependencies.
2. **Reflective Loop**: optimize/check alternation provides continuous self-correction.
3. **Multi-Model Fallback**: Skills try multiple models in order until one succeeds.
4. **State Separation**: Slow (roadmap) vs fast (active_task.json) parameters.
5. **Supervised Logging**: `[timestamp] [Supervised-PID:PID|||PLAN] [Sub-PID: SUBPID|||TASK/TOTAL]`
6. **Daemon Management**: Unified start/stop/status/cron across all skills.
7. **Differential Cron**: Health check intervals tuned per skill workload.

---

## File Structure (Per Skill)

```
<name>-loop/
├── README.md                          # Skill-specific documentation
├── SKILL.md                           # Core instruction set
├── prompt.md                          # Default loop prompt
└── scripts/
    ├── init_<name>_loop.cjs           # Initialize state files
    ├── dispatch_agent.sh              # Dispatch to CLI with fallback
    ├── run_daemon.py                  # Core daemon (optimize/check)
    ├── run_daemon.sh                  # Shell entry point
    ├── start_<name>_loop.sh           # Start daemon (tmux/nohup)
    ├── stop_<name>_loop.sh            # Stop daemon gracefully
    ├── status_<name>_loop.sh          # Check daemon status
    └── print_cron_entry.sh            # Print cron entries
```

---

*Part of the AgentHUD Autonomous Engineering Suite.*
