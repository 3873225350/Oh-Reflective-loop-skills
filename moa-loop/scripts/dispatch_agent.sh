#!/usr/bin/env bash
#================================================================
# MOA Loop v2.0 Dispatcher
# Architecture: 纵向时序迭代 + 横向DAG协同 + 共享黑板 + PEFT
#================================================================

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="${SKILL_DIR}/scripts"
MODE="${1:-optimize}"
LOOP_NAME="${2:-DEFAULT_MOA_ROADMAP}"
WORKSPACE="${WORKSPACE:-$(pwd)}"
CONFIG_FILE="${SCRIPT_DIR}/config.json"

export WORKSPACE LOOP_NAME MODE

STATE_DIR="${WORKSPACE}/.reflective-loop/state/${LOOP_NAME}"
LOG_DIR="${STATE_DIR}/dispatch_logs"
mkdir -p "${STATE_DIR}" "${LOG_DIR}" "${STATE_DIR}/iterations"

dispatch_log="${LOG_DIR}/moa-dispatch_${LOOP_NAME}_$(date +%Y%m%d_%H%M%S).log"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_dispatch() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [${BLUE}PROVIDER:moa${NC}] $1" | tee -a "${dispatch_log}"
}

log_success() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [${GREEN}SUCCESS${NC}] $1" | tee -a "${dispatch_log}"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [${RED}ERROR${NC}] $1" | tee -a "${dispatch_log}"
}

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  MOA Loop v2.0 — DAG + Blackboard + PEFT                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

log_dispatch "══════════ MOA v2.0 Dispatch Start ══════════"
log_dispatch "Mode: ${MODE}, Loop: ${LOOP_NAME}"

# 1. Detect available agents
log_dispatch "Detecting available agents..."
AGENTS=($(bash "${SCRIPT_DIR}/detect_agents.sh" 2>/dev/null | grep "^✅" | awk '{print $2}'))
log_dispatch "Available: ${AGENTS[*]:-none}"

if [[ ${#AGENTS[@]} -eq 0 ]]; then
    log_error "No agents available. Exiting."
    exit 1
fi

# 2. Initialize shared blackboard
export LOG_DIR
log_dispatch "Initializing shared blackboard..."
python3 -c "
import sys, json
sys.path.insert(0, '${SCRIPT_DIR}')
from core.shared_blackboard import SharedBlackboard
bb = SharedBlackboard(persist_path='${STATE_DIR}/blackboard.json')

# Register available agents
agents = '${AGENTS[*]}'.split()
config = json.load(open('${CONFIG_FILE}'))
for agent in agents:
    caps = config.get('agent_capabilities', {}).get(agent, {}).get('best_for', ['general'])
    bb.register_agent(agent, caps)

bb._maybe_persist()
print(f'Registered {len(agents)} agents')
"

# 3. Show DAG plan
log_dispatch "DAG Execution Plan:"
python3 -c "
import sys, json
sys.path.insert(0, '${SCRIPT_DIR}')
from core.dag_scheduler import DAGScheduler, DAG

config = json.load(open('${CONFIG_FILE}'))
dag = DAG.from_config(config.get('dag', {'nodes': []}))
scheduler = DAGScheduler(dag)
print(scheduler.visualize_ascii())
" 2>&1 | tee -a "${dispatch_log}"

# 4. Show iteration status
log_dispatch "Iteration Status:"
python3 -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}')
from core.iteration_manager import IterationManager
mgr = IterationManager('${STATE_DIR}/iterations', '${LOOP_NAME}')
print(mgr.show_status())
" 2>&1 | tee -a "${dispatch_log}"

# 5. Execute via DAG-driven daemon
log_dispatch "Launching DAG-driven execution (mode: ${MODE})..."
log_dispatch "══════════ Dispatch Complete ══════════"
