---
name: qwen-loop
description: Sets up and manages an autonomous scheduler loop based on reflective machine learning metaphors (Pretrained Backbone, Local Adapters, Error Banks). Use when asked to setup or manage a qwen-loop.
---

# Qwen Loop Skill (Reflective ML Edition)

This skill provides an automated framework for running an autonomous coding loop using Qwen CLI, heavily inspired by ML training principles.

## Architecture

The loop treats long-horizon agent work as a layered optimization process:

- **`roadmap.md` (Pretrained Backbone):** Slow parameters. Represents the global prior.
- **`active_task.json` (PEFT/LoRA Adapter):** Fast parameters. Represents localized execution state.
- **`failure_bank.json` (Reusable Failure Memory):** Prevents recurring mistakes.
- **`optimize` (Forward Pass):** Agent executes one verifiable slice.
- **`check` (Backward Signal):** Generates a **Local Patch** to guide the next pass.

## Qwen-Specific Implementation

| Aspect | Implementation |
|--------|---------------|
| **CLI Flags** | `qwen -c` or `qwen -r <thread>` with `-p` for prompt |
| **Model Fallback** | Qwen models (configurable) |
| **Session** | Single mode or multi-turn with thread files |
| **State** | `active_task.json` for fast adapter, `last_mode.txt` for mode state |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/dispatch_agent.sh` | Dispatch with Qwen-specific invoke_agent function |
| `scripts/run_daemon.sh` | Daemon loop with mode switching |
| `scripts/init_qwen_loop.cjs` | Initializes a new loop instance |

## Usage

```bash
# Start daemon for a loop
bash qwen-loop/scripts/run_daemon.sh <LOOP_NAME>

# Manual dispatch
bash qwen-loop/scripts/dispatch_agent.sh <optimize|check> <LOOP_NAME>
```