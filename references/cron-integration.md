# Cron Integration Guide (All Skills)

Use this reference when you want system-level scheduling for any reflective loop skill.

## Principle

`cron` sits outside the skill daemon, not inside it. The daemon owns the loop; cron owns supervision.

| Layer | Responsibility |
|-------|---------------|
| **Daemon** | Recurring loop, state management, logs, lock files, agent dispatch |
| **tmux/nohup** | Detached runtime so the daemon survives shell exit |
| **cron** | Start after reboot, health check, auto-restart on failure |

## When cron helps

- Machine reboots often — daemon should auto-start
- Daemon crashes — cron brings it back
- Loop should only run during certain hours
- Multiple skills need independent supervision

## When cron is NOT needed

- Manual background daemon is enough
- Loop is experimental and short-lived
- Using systemd or another process supervisor instead

## Quick Setup

Every skill ships a `print_cron_entry.sh` that outputs ready-to-use cron entries:

```bash
# Print cron entries for any skill
bash <skill>-loop/scripts/print_cron_entry.sh

# Add to crontab
bash <skill>-loop/scripts/print_cron_entry.sh | crontab -
```

## Per-Skill Cron Strategy

Each skill has a health-check interval tuned to its workload:

| Skill | Interval | Why |
|-------|----------|-----|
| gemini-loop | `*/5` | Reference agent, fast iteration |
| codex-loop | `*/10` | Balanced, production-stable |
| claude-loop | `*/10` | Production-grade, stable priority |
| cursor-loop | `*/15` | IDE integration, less frequent |
| kimi-loop | `*/15` | Long-context tasks, wider interval |
| minimax-loop | `*/5` | Lightweight, fast patrol |
| qwen-loop | `*/10` | Balanced strategy |
| moa-loop | `*/5` | Multi-agent orchestration, needs frequent checks |

## What cron entries look like

Each skill generates two entries:

```cron
# 1. Auto-start after reboot
@reboot cd /workspace && <SKILL>_LOOP_WORKSPACE=/workspace <SKILL>_LOOP_LAUNCHER=tmux bash /path/to/start_*.sh

# 2. Periodic health check + auto-restart
*/N * * * * cd /workspace && <SKILL>_LOOP_WORKSPACE=/workspace bash /path/to/status_*.sh >/tmp/<skill>-loop-status.log 2>&1 || bash /path/to/start_*.sh >>/tmp/<skill>-loop-status.log 2>&1
```

## Running Multiple Skills

To supervise all skills at once:

```bash
# Generate combined crontab
{
  for skill in gemini codex claude cursor kimi minimax qwen moa; do
    bash ${skill}-loop/scripts/print_cron_entry.sh
    echo ""
  done
} | crontab -
```

## Environment Variables

Each skill respects `<SKILL>_LOOP_*` environment variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `<SKILL>_LOOP_WORKSPACE` | Working directory | `$PWD` |
| `<SKILL>_LOOP_STATE_DIR` | State directory | `.<skill>-loop/state` |
| `<SKILL>_LOOP_LOOP_NAME` | Loop instance name | `OPTIMIZE_ROADMAP` |
| `<SKILL>_LOOP_INTERVAL` | Tick interval (seconds) | `60` |
| `<SKILL>_LOOP_LAUNCHER` | `tmux`, `nohup`, or `auto` | `auto` |

## Warning

Keep cron entries simple. Do not embed task logic in crontab.
Put loop behavior in `<skill>-loop/prompt.md` and let the daemon read it.
Treat `cron` as a supervisor and `tmux`/`nohup` as the detached runtime.
