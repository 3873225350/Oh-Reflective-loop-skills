#!/usr/bin/env node
//================================================================
// MOA Loop v2.0 Initializer
// Architecture: 纵向时序迭代 + 横向DAG协同 + 共享黑板 + PEFT
//================================================================

const fs = require('fs');
const path = require('path');

const loopName = process.argv[2] || 'DEFAULT_MOA_ROADMAP';
const workspace = process.argv[3] || process.cwd();

const stateDir = path.join(workspace, '.reflective-loop', 'state', loopName);
const subTasksDir = path.join(stateDir, 'sub-tasks');
const dispatchLogsDir = path.join(stateDir, 'dispatch_logs');
const logsDir = path.join(stateDir, 'logs');
const iterationsDir = path.join(stateDir, 'iterations');
const snapshotsDir = path.join(stateDir, 'iterations', 'snapshots');

// Create all directories
[stateDir, subTasksDir, dispatchLogsDir, logsDir, iterationsDir, snapshotsDir].forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`Created: ${dir}`);
    }
});

// Create default roadmap (主脊 = 预训练权重)
const roadmapContent = `# MOA Loop Roadmap v2.0

**Plan ID**: \`moa-optimize\`
**Active Task**: \`T1\`
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
\`\`\`
Layer 0 (PARALLEL): [research]
Layer 1 (SERIAL):   [code]        ← depends on research
Layer 2 (PARALLEL): [test, doc]   ← both depend on code
Layer 3 (SERIAL):   [review]      ← depends on test + doc
\`\`\`

## PEFT Configuration
- Roadmap主脊冻结: true
- Adapter作用域: sub-tasks
- 每轮最大变更: 5
`;

const roadmapPath = path.join(stateDir, `${loopName}.md`);
if (!fs.existsSync(roadmapPath)) {
    fs.writeFileSync(roadmapPath, roadmapContent);
    console.log(`Created: ${roadmapPath}`);
}

// Create last_mode.txt
const lastModePath = path.join(stateDir, 'last_mode.txt');
if (!fs.existsSync(lastModePath)) {
    fs.writeFileSync(lastModePath, 'optimize');
    console.log(`Created: ${lastModePath}`);
}

// Create active_task.json
const activeTaskPath = path.join(stateDir, 'active_task.json');
if (!fs.existsSync(activeTaskPath)) {
    const activeTask = {
        plan_id: 'moa-optimize',
        task_id: 'T1',
        status: 'pending',
        epoch: 0,
        architecture: 'v2.0-DAG-Blackboard-PEFT',
        frozen_backbone: [],
        adapters: {},
        created_at: new Date().toISOString()
    };
    fs.writeFileSync(activeTaskPath, JSON.stringify(activeTask, null, 2));
    console.log(`Created: ${activeTaskPath}`);
}

// Initialize blackboard.json
const blackboardPath = path.join(stateDir, 'blackboard.json');
if (!fs.existsSync(blackboardPath)) {
    const blackboard = {
        timestamp: new Date().toISOString(),
        knowledge: {},
        agents: {},
        task_results: {},
        event_log: []
    };
    fs.writeFileSync(blackboardPath, JSON.stringify(blackboard, null, 2));
    console.log(`Created: ${blackboardPath}`);
}

// Initialize iteration database directory marker
const dbMarkerPath = path.join(iterationsDir, '.gitkeep');
if (!fs.existsSync(dbMarkerPath)) {
    fs.writeFileSync(dbMarkerPath, '');
}

console.log(`\n✅ MOA Loop v2.0 "${loopName}" initialized!`);
console.log(`\nArchitecture:`);
console.log(`  纵向: Markdown → JSON → SQL (训练循环)`);
console.log(`  横向: DAG调度 (计算图)`);
console.log(`  Roadmap = 预训练权重 (冻结)`);
console.log(`  Sub-task = PEFT Adapter (微调)`);
console.log(`\nState: ${stateDir}`);
console.log(`\nTo start the v2 daemon:`);
console.log(`  bash moa-loop/scripts/run_daemon.sh ${loopName}`);
