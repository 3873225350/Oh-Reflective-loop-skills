const fs = require('fs');
const path = require('path');

async function run() {
  const workspace = process.cwd();
  const loopName = process.argv[2] || 'DEFAULT_ROADMAP';
  console.log(`[Gemini-Loop] Initializing Reflective Loop environment in: ${workspace} for loop: ${loopName}`);

  const stateDir = path.join(workspace, '.gemini-loop', 'state', loopName);
  const taskDir = path.join(stateDir, 'sub-tasks');

  // 1. Create directory structure
  [stateDir, taskDir, path.join(stateDir, 'logs'), path.join(stateDir, 'dispatch_logs')].forEach(dir => {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  });

  // 2. Create Initial Roadmap
  const roadmapPath = path.join(stateDir, `${loopName}.md`);
  if (!fs.existsSync(roadmapPath)) {
    fs.writeFileSync(roadmapPath, `# AgentHUD Integration Roadmap (${loopName})

**Plan ID**: \`${loopName}-${Date.now()}\`
**Status**: \`M1: Initializing\`
**Active Task**: \`INIT-001\`

## Milestones
- [ ] **INIT-001**: Define project goals.
`);
  }

  // 3. Create Failure Bank
  const failureBankPath = path.join(stateDir, 'failure_bank.json');
  if (!fs.existsSync(failureBankPath)) {
    fs.writeFileSync(failureBankPath, JSON.stringify({ schema_version: 1, failures: [] }, null, 2));
  }

  // 4. Create Active Task Adapter
  const activeTaskPath = path.join(stateDir, 'active_task.json');
  if (!fs.existsSync(activeTaskPath)) {
    fs.writeFileSync(activeTaskPath, JSON.stringify({
      active_task_id: "INIT-001",
      status: "planned",
      local_patches: []
    }, null, 2));
  }

  console.log(`[Gemini-Loop] Done. You can now start the daemon: bash .gemini-loop/scripts/run_daemon.sh ${loopName}`);
}

run().catch(console.error);
