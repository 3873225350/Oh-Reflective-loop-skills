---
name: gemini-loop
description: Sets up and manages an autonomous scheduler loop based on reflective machine learning metaphors (Pretrained Backbone, Local Adapters, Error Banks). Use when asked to setup or manage a gemini-loop.
---

# Gemini Loop Skill (Reflective ML Edition)

This skill provides an automated framework for running an autonomous coding loop using Gemini CLI, heavily inspired by ML training principles.

## Architecture

The loop treats long-horizon agent work as a layered optimization process:

- **`roadmap.md` (Pretrained Backbone):** Slow parameters. Represents the global prior.
- **`active_task.json` (PEFT/LoRA Adapter):** Fast parameters. Represents localized execution state.
- **`failure_bank.json` (Reusable Failure Memory):** Prevents recurring mistakes.
- **`optimize` (Forward Pass):** Agent executes one verifiable slice.
- **`check` (Backward Signal):** Generates a **Local Patch** to guide the next pass.

## Shared Templates Architecture

This skill uses the **shared templates** system to avoid code duplication while preserving Gemini's unique characteristics:

```
Reflective-loop/shared-templates/
├── daemon_framework.sh        # Generic daemon (mode switching, scheduling)
├── dispatch_framework.sh     # Generic dispatch (logging, error handling)
└── skill_adapters/
    └── gemini_adapter.sh      # Gemini-specific: --resume latest, model fallback
```

### Gemini-Specific Implementation

| Aspect | Implementation |
|--------|---------------|
| **CLI Flags** | `--resume latest --approval-mode yolo --output-format text` |
| **Model Fallback** | `gemini-3.1-pro-preview` → `gemini-3-flash-preview` → ... → `gemini-2.5-flash-lite` |
| **Session** | Uses `--resume latest` for single-session continuation |
| **State** | `active_task.json` for fast adapter, `last_mode.txt` for mode state |

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/dispatch_agent.sh` | Sources shared `dispatch_framework.sh`, overrides gemini-specific functions |
| `scripts/run_daemon.sh` | Sources shared `daemon_framework.sh`, calls dispatch_agent.sh |
| `scripts/init_gemini_loop.cjs` | Initializes a new loop instance |

## Usage

```bash
# Start daemon for a loop
bash gemini-loop/scripts/run_daemon.sh <LOOP_NAME>

# Manual dispatch
bash gemini-loop/scripts/dispatch_agent.sh <optimize|check> <LOOP_NAME>
```