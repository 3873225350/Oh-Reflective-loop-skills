---
name: codex-loop
description: Sets up and manages an autonomous scheduler loop based on reflective machine learning metaphors (Pretrained Backbone, Local Adapters, Error Banks) for Codex.
---

# Codex Loop Skill (Reflective ML Edition)

This skill provides an automated framework for running an autonomous coding loop using Codex CLI, heavily inspired by ML training principles.

## Architecture

The loop treats long-horizon agent work as a layered optimization process:

- **`CODEX_ROADMAP.md` (Pretrained Backbone):** Slow parameters. Represents the global prior, stable constraints, and overall mission. Only updated when structural failures are proven.
- **`active_task.json` (PEFT/LoRA Adapter):** Fast parameters. Represents the localized execution state. Continually updated with assumed risks, targets, and immediate actions.
- **`failure_bank.json` (Reusable Failure Memory):** A global registry of recurrent patterns and mistakes to prevent looping errors.
- **`optimize` (Forward Pass):** Agent executes precisely one bounded slice of the `active_task.json`.
- **`check` (Backward Signal):** Agent inspects the actual outcome vs the intended objective. Instead of just passing or failing, it produces a **Local Patch** (e.g. `scope_patch`, `prompt_patch`) which is passed into the `active_task.json` for the next forward pass.

## Reflective Loop: optimize ↔ check Alternation

The daemon alternates between two modes each tick:

1. **optimize (Forward Pass)**: Implementation agent reads `failure_bank.json` and `local_patches` from `active_task.json`, then executes one bounded slice of work.
2. **check (Backward Signal)**: Checker agent reviews the implementation, computes the "loss" between target and actual state, and writes `local_patches` if corrections are needed.

## Quick Start

To initialize the reflective loop in the current workspace:

```bash
node <path-to-skill>/scripts/init_codex_loop.cjs [LOOP_NAME]
```

Then start the daemon:

```bash
bash .codex-loop/scripts/run_daemon.sh [LOOP_NAME]
```

## State Files

After initialization, the following state files are created:

```
.codex-loop/
├── prompt.md                    # Default loop instructions
└── state/
    └── <LOOP_NAME>/
        ├── <LOOP_NAME>.md       # Roadmap (Pretrained Backbone)
        ├── active_task.json     # PEFT Adapter with local_patches
        ├── failure_bank.json    # Failure memory
        ├── last_mode.txt        # optimize/check alternation state
        ├── daemon.pid           # Daemon process ID
        ├── active.log           # Symlink to current log
        ├── logs/                # Historical logs
        ├── dispatch_logs/       # Agent dispatch logs
        └── sub-tasks/           # Sub-task JSON files
```

## Multi-Model Fallback

The dispatcher tries models in order until one succeeds:
1. `o3`
2. `o4-mini`
3. `gpt-4.1`
4. `gpt-4.1-mini`
5. `gpt-4.1-nano`

## Scripts

| Script | Purpose |
|--------|---------|
| `init_codex_loop.cjs` | Initialize state directory and files |
| `run_daemon.sh` | Start the daemon (calls `run_daemon.py`) |
| `run_daemon.py` | Core daemon with optimize/check alternation |
| `dispatch_agent.sh` | Dispatch to Codex with multi-model fallback |
| `start_codex_loop.sh` | Start daemon in tmux/nohup |
| `stop_codex_loop.sh` | Stop daemon gracefully |
| `status_codex_loop.sh` | Check daemon status |
| `monitor_codex_loop.sh` | Real-time monitoring panel |

---

*Built with ❤️ by the AgentHUD Team using Codex-Reflective-Loop.*
