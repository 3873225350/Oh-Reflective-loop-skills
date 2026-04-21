#!/usr/bin/env node
//================================================================
// MOA Loop Initializer
// Creates a new MOA loop with agent detection
//================================================================

const fs = require('fs');
const path = require('path');

const loopName = process.argv[2] || 'DEFAULT_MOA_ROADMAP';
const workspace = process.argv[3] || process.cwd();

const stateDir = path.join(workspace, '.reflective-loop', 'state', loopName);
const subTasksDir = path.join(stateDir, 'sub-tasks');
const dispatchLogsDir = path.join(stateDir, 'dispatch_logs');
const logsDir = path.join(stateDir, 'logs');

// Create directories
[stateDir, subTasksDir, dispatchLogsDir, logsDir].forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`Created: ${dir}`);
    }
});

// Create default roadmap
const roadmapContent = `# MOA Loop Roadmap

**Plan ID**: \`moa-optimize\`
**Active Task**: \`T1\`
**Type**: Mixture of Agents (MOA)

This loop uses a mixture of available AI agents to coordinate work.

## Current Progress
- [ ] **T1** — Initialize MOA Loop
- [ ] **T2** — Detect Available Agents
- [ ] **T3** — Configure Primary Agent
- [ ] **T4** — Run First Task

---

## Agent Status
Detected agents will be listed here after first run.

## Sub-Tasks
Sub-tasks will be created dynamically.
`;

const roadmapPath = path.join(stateDir, `${loopName}.md`);
if (!fs.existsSync(roadmapPath)) {
    fs.writeFileSync(roadmapPath, roadmapContent);
    console.log(`Created: ${roadmapPath}`);
}

// Create initial last_mode.txt
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
        local_patches: [],
        created_at: new Date().toISOString()
    };
    fs.writeFileSync(activeTaskPath, JSON.stringify(activeTask, null, 2));
    console.log(`Created: ${activeTaskPath}`);
}

console.log(`\n✅ MOA Loop "${loopName}" initialized successfully!`);
console.log(`\nState directory: ${stateDir}`);
console.log(`\nTo start the daemon:`);
console.log(`  bash moa-loop/scripts/run_daemon.sh ${loopName}`);