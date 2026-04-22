# MOA Loop Roadmap v2.0

**Plan ID**: `moa-optimize`
**Active Task**: `T1`
**Type**: Mixture of Agents (MOA) — DAG + Blackboard + PEFT

## Architecture
- **纵向**: Markdown → JSON → SQL, optimize/check 交替迭代
- **横向**: DAG调度, 无依赖并行, 有依赖串行
- **Roadmap主脊**: 冻结 (= 预训练权重)
- **Sub-task Adapter**: PEFT微调 (= 只改局部)

## Current Progress
- [ ] **T1** — Initialize MOA Loop v2.0
- [ ] **T2** — Detect Available Agents
- [ ] **T3** — Freeze Roadmap Backbone
- [ ] **T4** — Run DAG Execution
- [ ] **T5** — PEFT Adapter Adaptation
- [ ] **T6** — Verify & Check Results

---

## Agent Status
Detected agents will be listed here after first run.

## DAG Structure
```
Layer 0 (PARALLEL): [research]
Layer 1 (SERIAL):   [code]        ← depends on research
Layer 2 (PARALLEL): [test, doc]   ← both depend on code
Layer 3 (SERIAL):   [review]      ← depends on test + doc
```

## PEFT Configuration
- Roadmap主脊冻结: true
- Adapter作用域: sub-tasks
- 每轮最大变更: 5
