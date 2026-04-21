---
name: moa-loop
description: Mixture of Agents Loop v2.0 - Coordinates multiple AI agents with FIFO + SQLite hybrid communication, task routing, and collaborative writing.
---

# MOA Loop v2.0 (Mixture of Agents)

## Architecture: FIFO + SQLite Hybrid Communication

```
┌─────────────────────────────────────────────────────────────┐
│                      MOA Bus System                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🚀 FIFO (Real-time Messages)                              │
│  ────────────────────────────────────                      │
│  /tmp/moa_bus/{bus}/fifos/                               │
│  ├── gemini.fifo     (微秒级延迟)                         │
│  ├── claude.fifo                                          │
│  ├── qwen.fifo                                            │
│  └── coordinator.fifo                                     │
│                                                             │
│  → cat /tmp/moa_bus/default/fifos/gemini.fifo             │
│  → echo '{"msg":"task"}' > /tmp/moa_bus/default/fifos/gemini.fifo │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  💾 SQLite (Persistent Storage)                            │
│  ─────────────────────────────────────                     │
│  /tmp/moa_bus/{bus}/context.db                           │
│                                                             │
│  Tables:                                                   │
│  ├── messages    (消息历史)                                 │
│  ├── agents      (智能体注册)                              │
│  ├── knowledge   (共享知识库)                              │
│  ├── tasks       (任务状态)                                │
│  └── state       (全局状态)                               │
│                                                             │
│  → sqlite3 /tmp/moa_bus/default/context.db "SELECT * FROM agents" │
│  → DB Browser for SQLite 可视化                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Initialize bus
moa_bus.sh init

# Register agents
moa_bus.sh register gemini coding,reasoning
moa_bus.sh register claude writing,analysis

# Post messages (FIFO)
moa_bus.sh post gemini task "Implement feature X"

# Knowledge base (SQLite)
moa_bus.sh knowledge add "project_goal" "Complete optimization"
moa_bus.sh knowledge list

# Tasks (SQLite)
moa_bus.sh task create T1 "Build component" "gemini"
moa_bus.sh task list

# Query directly with SQL
sqlite3 /tmp/moa_bus/default/context.db "SELECT * FROM agents"
```

## Agent Capabilities

| Agent | Strengths | Best For | Context | Cost |
|-------|-----------|----------|---------|------|
| gemini | reasoning, code, fast | coding, analysis | 1M | medium |
| claude | analysis, writing, safety | writing, review | 200K | high |
| qwen | coding, math, multilingual | coding, math | 131K | low |
| kimi | long_context, summarization | research, docs | 2M | medium |
| cursor | IDE integration, refactoring | code edit | 100K | medium |
| minimax | speed, quick_response | quick tasks | 10K | low |

## Communication Flow

```
┌─────────────┐
│ Coordinator │
└──────┬──────┘
       │
       ├── FIFO ──> gemini.fifo (real-time message)
       │
       ├── SQLite messages table (persistent history)
       │
       ├── SQLite agents table (registry)
       │
       └── SQLite knowledge table (shared context)
```

## Scripts

| Script | Purpose |
|--------|---------|
| `moa_bus.py` | Core FIFO + SQLite engine |
| `moa_bus.sh` | CLI wrapper |
| `collab_writer.sh` | Multi-agent collaborative writing |
| `detect_agents.sh` | Auto-detect available agents |

## Usage

```bash
# Detect available agents
bash moa-loop/scripts/detect_agents.sh

# Run MOA dispatch
bash moa-loop/scripts/dispatch_agent.sh <optimize|check> <LOOP_NAME>

# Start MOA daemon
bash moa-loop/scripts/run_daemon.sh <LOOP_NAME>
```

## Configuration

Edit `config.json`:
- `primary_agent`: Main agent for primary tasks
- `enabled_agents`: List of agents to use
- `max_parallel`: Max parallel workers
- `task_routing`: Task-to-agent mapping