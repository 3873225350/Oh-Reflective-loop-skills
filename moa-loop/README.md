# MOA Loop v2.0 (Mixture of Agents)

![AgentHUD Banner](https://raw.githubusercontent.com/Harzva/agent-hud/main/media/agenthud.svg)

An intelligent orchestration loop that dynamically coordinates multiple AI agents based on availability, capability matching, and task requirements.

---

## 🎯 What is MOA?

MOA (Mixture of Agents) v2.0 is an enhanced orchestration system that:

1. **Auto-Detection** - Automatically discovers which AI agents are installed
2. **Capability Matching** - Routes tasks to agents based on their strengths
3. **Parallel Execution** - Runs multiple agents simultaneously for complex tasks
4. **Smart Fallback** - Automatically falls back if primary agent fails
5. **Result Aggregation** - Collects and summarizes results from multiple agents

## 🧠 Agent Capabilities

| Agent | Strengths | Best For | Max Context | Cost Tier |
|-------|-----------|----------|------------|----------|
| 🔮 **gemini** | Reasoning, code, fast | Coding, analysis | 1M tokens | Medium |
| 📝 **claude** | Analysis, writing, safety | Writing, review | 200K tokens | High |
| 💻 **qwen** | Coding, math, multilingual | Coding, math | 131K tokens | Low |
| 📚 **kimi** | Long context, summarization | Research, docs | 2M tokens | Medium |
| 🎯 **cursor** | IDE integration, refactoring | Code edit | 100K tokens | Medium |
| ⚡ **minimax** | Speed, quick response | Quick tasks | 10K tokens | Low |

## 🚀 Quick Start

### 1. Detect Available Agents
```bash
bash moa-loop/scripts/detect_agents.sh
```
Output:
```
🔍 Detecting available AI agents...
✅ gemini is available
✅ claude is available
✅ qwen is available
❌ cursor is not available
📊 Summary: gemini claude qwen
```

### 2. Configure (Optional)
Edit `moa-loop/scripts/config.json`:
```json
{
  "primary_agent": "gemini",
  "enabled_agents": ["gemini", "claude", "qwen", "kimi"],
  "max_parallel": 3,
  "agent_capabilities": { ... },
  "task_routing": {
    "coding": ["gemini", "claude", "qwen"],
    "research": ["kimi", "gemini"],
    "quick": ["minimax", "qwen"]
  }
}
```

### 3. Initialize a Loop
```bash
node moa-loop/scripts/init_moa_loop.cjs MY_PROJECT
```

### 4. Run the Daemon
```bash
bash moa-loop/scripts/run_daemon.sh MY_PROJECT
```

## 📁 State Files

```
.reflective-loop/state/{LOOP_NAME}/
├── dispatch_logs/
│   ├── moa-dispatch_*.log      # Main dispatch log
│   ├── gemini-*.log              # Per-agent logs
│   ├── claude-*.log
│   └── ...
└── logs/
    └── moa-loop-*.log           # Daemon supervision logs
```

## 🔍 Example Output

```
╔════════════════════════════════════════════════════════════════╗
║  MOA (Mixture of Agents) Dispatcher v2.0                     ║
╚════════════════════════════════════════════════════════════════╝
[2026-04-22 10:30:15] [PROVIDER:moa] ══════════ MOA Dispatch Start ══════════
[2026-04-22 10:30:15] [PROVIDER:moa] Mode: optimize, Loop: MY_PROJECT
[2026-04-22 10:30:15] [PROVIDER:moa] 📊 Agent Status:
[2026-04-22 10:30:15] [PROVIDER:moa]    Available: gemini claude qwen kimi
[2026-04-22 10:30:15] [PROVIDER:moa]    Primary: gemini
[2026-04-22 10:30:15] [PROVIDER:moa]    Max Parallel: 3
[2026-04-22 10:30:15] [PROVIDER:moa] 🚀 Trying primary agent: gemini
[2026-04-22 10:30:15] [PROVIDER:moa] ▶ Invoking gemini...
[2026-04-22 10:30:45] [SUCCESS] ✓ gemini completed in 30s
[2026-04-22 10:30:45] [PROVIDER:moa] ══════════ Dispatch Complete ══════════
```

## 🔧 Task Routing

MOA automatically routes tasks based on type:

```json
"task_routing": {
  "coding":       ["gemini", "claude", "qwen", "cursor"],
  "writing":      ["claude", "gemini", "qwen"],
  "analysis":     ["claude", "gemini", "kimi"],
  "research":     ["kimi", "gemini", "claude"],
  "quick":       ["minimax", "qwen"],
  "default":     ["gemini", "claude"]
}
```

## 🔄 Retry Policy

Configure automatic retry on failure:

```json
"retry_policy": {
  "max_retries": 3,
  "retry_delay": 5,
  "escalate_on_failure": true
}
```

*Built with ❤️ by the AgentHUD Team using MoA Architecture v2.0*