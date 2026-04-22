---
name: moa-loop
description: MOA Loop v2.0 — 纵向时序迭代 + 横向DAG协同 + 共享黑板 + PEFT微调的多Agent协作框架
---

# MOA Loop v2.0 (Mixture of Agents)

## 核心设计思想

本架构将 **ML 训练范式** 搬到 Agent 协作调度上：

| ML 概念 | Agent Loop 对应 | 说明 |
|---------|----------------|------|
| **预训练权重 (Base Weights)** | Roadmap 主脊任务 | 冻结、不轻易改动、定义整体方向 |
| **PEFT / LoRA / Adapter** | 实验反思微调计划 | 只改局部、不动主架构、快速适应 |
| **微调数据** | Sub-tasks / 实验结果 | 具体任务、驱动 adapter 更新 |
| **训练循环 (Epoch)** | 纵向 optimize/check 交替 | 时间轴串行、一轮推进一轮 |
| **计算图 (DAG)** | 横向任务依赖图 | 无依赖并行、有依赖串行 |

## 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│                   纵向迭代 (训练循环)                         │
│  Epoch N: optimize → check → snapshot → next epoch          │
│  数据流: Markdown → JSON → SQL                              │
│  Roadmap冻结 + PEFT Adapter微调                              │
├─────────────────────────────────────────────────────────────┤
│                   横向DAG (计算图)                            │
│  Layer 0: [research]              ← PARALLEL (无依赖)        │
│  Layer 1: [code]                  ← SERIAL (依赖research)    │
│  Layer 2: [test, doc]             ← PARALLEL (同依赖code)    │
│  Layer 3: [review]                ← SERIAL (依赖test+doc)    │
├─────────────────────────────────────────────────────────────┤
│                   通信层                                      │
│  横向: 共享黑板 (Shared Blackboard) — 低延迟、高并发          │
│  纵向: JSON + SQLite — 可持久、可回溯                         │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Initialize loop
node moa-loop/scripts/init_moa_loop.cjs MY_PROJECT

# 2. Detect agents
bash moa-loop/scripts/detect_agents.sh

# 3. Start v2 daemon (DAG + Blackboard + PEFT)
LOOP_NAME=MY_PROJECT INTERVAL=60 WORKSPACE=$(pwd) \
  bash moa-loop/scripts/run_daemon.sh MY_PROJECT
```

## Core Modules

| Module | File | 职责 |
|--------|------|------|
| **DAG Scheduler** | `core/dag_scheduler.py` | 横向DAG调度，拓扑排序，并行执行 |
| **Shared Blackboard** | `core/shared_blackboard.py` | 共享黑板，中心化Agent通信 |
| **Iteration Manager** | `core/iteration_manager.py` | 纵向迭代，Roadmap冻结，PEFT微调 |

## CLI Tools

```bash
# DAG analysis
python3 moa-loop/scripts/core/dag_scheduler.py config.json --visualize
python3 moa-loop/scripts/core/dag_scheduler.py config.json --analyze

# Blackboard management
python3 moa-loop/scripts/core/shared_blackboard.py summary
python3 moa-loop/scripts/core/shared_blackboard.py write key value agent_name
python3 moa-loop/scripts/core/shared_blackboard.py agents

# Iteration management
python3 moa-loop/scripts/core/iteration_manager.py status <state_dir>
python3 moa-loop/scripts/core/iteration_manager.py history <state_dir> 20
python3 moa-loop/scripts/core/iteration_manager.py rollback <state_dir> 3
```

## Configuration

编辑 `moa-loop/scripts/config.json`:

```json
{
  "dag": {
    "nodes": [
      {"id": "research", "type": "research", "deps": []},
      {"id": "code", "type": "coding", "deps": ["research"]},
      {"id": "test", "type": "coding", "deps": ["code"]},
      {"id": "doc", "type": "writing", "deps": ["code"]},
      {"id": "review", "type": "analysis", "deps": ["test", "doc"]}
    ]
  },
  "peft": {
    "freeze_roadmap": true,
    "adapter_scope": "sub-tasks",
    "max_adapter_changes_per_epoch": 5
  }
}
```

## Agent Capabilities

| Agent | Strengths | Best For | Cost |
|-------|-----------|----------|------|
| gemini | reasoning, code, fast | coding, analysis | medium |
| claude | analysis, writing, safety | writing, review | high |
| qwen | coding, math, multilingual | coding, math | low |
| kimi | long_context, summarization | research, docs | medium |
| cursor | IDE integration, refactoring | code edit | medium |
| minimax | speed, quick_response | quick tasks | low |
