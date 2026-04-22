# MOA Loop v2.0 (Mixture of Agents)

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
node moa-loop/scripts/init_moa_loop.cjs MY_PROJECT

# Start daemon
bash moa-loop/scripts/run_daemon.sh MY_PROJECT
```

## Modules

- `core/dag_scheduler.py` — DAG scheduling with topological sort
- `core/shared_blackboard.py` — Centralized agent communication
- `core/iteration_manager.py` — Epoch management + PEFT adaptation
- `run_daemon_v2.py` — Main loop orchestrator

## DAG Example

```
research ──→ code ──┬──→ test  ──┬──→ review
                    └──→ doc   ──┘
```

- Layer 0: `research` (no deps → parallel)
- Layer 1: `code` (depends on research → serial)
- Layer 2: `test`, `doc` (both depend on code → parallel)
- Layer 3: `review` (depends on test + doc → serial)

## PEFT Fine-Tuning

```
Roadmap Backbone (FROZEN = pretrained weights)
├── T1: Core task A  ← cannot modify
├── T2: Core task B  ← cannot modify
└── T3: Core task C  ← cannot modify

Sub-task Adapters (TRAINABLE = PEFT)
├── A1: Adapt based on experiment results
├── A2: Local plan adjustments only
└── A3: Task-specific lightweight adaptation
```

## Communication Layers

- **Horizontal** (real-time): Shared Blackboard — O(1) channels for N agents
- **Vertical** (persistent): JSON + SQLite — versioned, auditable, recoverable

*Built with AgentHUD MoA Architecture v2.0*
