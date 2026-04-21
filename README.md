# codex-loop

`codex-loop` is a Codex skill for recurring, plan-driven iteration.

It is the Codex-side counterpart to a `/loop` workflow:

- read one active plan
- inspect recent evolution notes
- execute one bounded slice
- write the next evolution note
- prepare the next handoff

It also includes an optional automation runner that can periodically resume the same Codex thread.

## Package contents

- `SKILL.md`
- `agents/openai.yaml`
- `references/automation-layout.md`
- `references/cron-integration.md`
- `references/evolution-template.md`
- `references/workspace-shell.md`
- `scripts/codex_loop_automation.py`
- `scripts/monitor_codex_loop.sh`
- `scripts/print_cron_entry.sh`
- `scripts/start_codex_loop.sh`
- `scripts/status_codex_loop.sh`
- `scripts/stop_codex_loop.sh`

## Install shape

This repository is packaged so it can be copied or installed into:

```text
~/.codex/skills/codex-loop/
```

## Install with native skill install

If your Codex build exposes the native skill installer, install directly from GitHub with:

```bash
skill install https://github.com/Harzva/codex-loop-skill
```

After installation, restart Codex to pick up the new skill.

## Manual usage

Example prompt:

```text
Use codex-loop to continue the active plan at .claude/plans/active-example-plan.md. Read the latest evolution note, complete one bounded iteration, write the next evolution note, and prepare the next handoff.
```

## Automation usage

Create a recurring prompt file in the target workspace:

```text
.codex-loop/prompt.md
```

Example:

```text
基于 .claude/plans/active-example-plan.md 继续一次 loop 迭代。
先读取最近的 evolution 记录；
本轮只完成一个最小可验证推进；
完成后更新 evolution note，并给出下一轮 handoff。
```

Then run:

```bash
bash ~/.codex/skills/codex-loop/scripts/start_codex_loop.sh
bash ~/.codex/skills/codex-loop/scripts/status_codex_loop.sh
bash ~/.codex/skills/codex-loop/scripts/monitor_codex_loop.sh --watch
bash ~/.codex/skills/codex-loop/scripts/stop_codex_loop.sh
```

The default automation layout is documented in `references/automation-layout.md`.

## Why this model is powerful

The key idea in `codex-loop` is:

- keep the outer loop executor stable
- change the inner task definition by editing the prompt file

That means you usually do **not** need to restart the daemon or abandon the existing thread just to change the work.

What stays stable:

- the daemon process
- the current Codex thread
- the state directory
- the log files

What can change live between ticks:

- the active plan path
- the iteration objective
- the review criteria
- whether the next pass focuses on implementation, review, cleanup, or another bounded task
- how much detail the logs or handoff should include

In other words:

`codex-loop` treats the daemon as the outer executor and `prompt.md` as the hot-swappable inner contract.

## Sticky task continuity

One important refinement from real long-running use:

- the loop should not pick a brand-new task every tick just because the prompt file contains many candidates
- the daemon should keep a sticky active task across ticks until that task is done, blocked, or intentionally deferred

Recommended rule for `prompt.md`:

- treat the task list as a pool
- but also maintain one active task state
- if the previous task is still unfinished and not blocked, continue it first
- only branch to another task after the current one is marked done, blocked, or explicitly deferred with a reason

This keeps `codex-loop` from turning into a context-switching backlog spinner. In practice it behaves more like:

- one outer daemon
- one persistent Codex thread
- one hot-swappable prompt contract
- one sticky active task until closure

That combination is what makes long unattended iteration actually accumulate.

## Monitoring and live logs

`codex-loop` runs as a background daemon, so it does not keep printing into your current shell by default.

Use these commands after startup:

```bash
bash ~/.codex/skills/codex-loop/scripts/status_codex_loop.sh
bash ~/.codex/skills/codex-loop/scripts/monitor_codex_loop.sh
```

This prints a status snapshot with:

- whether the daemon is running
- the current PID
- whether the daemon is in `tick` or `sleeping`
- the latest `raw_log_path`
- the latest `last_message_file`

To continuously watch the daemon output:

```bash
tail -f /absolute/workspace/.codex-loop/state/logs/daemon_stdout.log
```

To continuously watch one tick's raw event log:

```bash
tail -f /absolute/workspace/.codex-loop/state/logs/tick_YYYYMMDD_HHMMSS.log
```

## Optional cron integration

`codex-loop` already has its own daemon timer, so cron is optional.

Use cron only as an outer scheduler when you want:

- start-on-boot
- periodic health checks
- scheduled start/stop windows

Do not use cron to replace the daemon's thread-aware loop logic.

Print example cron entries with:

```bash
bash ~/.codex/skills/codex-loop/scripts/print_cron_entry.sh
```

See `references/cron-integration.md` for the recommended pattern.
