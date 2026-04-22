#!/usr/bin/env bash
#================================================================
# MOA Loop Monitor — DAG + Blackboard + PEFT Dashboard
#================================================================
set -euo pipefail

WORKSPACE="${MOA_LOOP_WORKSPACE:-$PWD}"
STATE_DIR="${MOA_LOOP_STATE_DIR:-${WORKSPACE}/.moa-loop/state}"
LOOP_NAME="${MOA_LOOP_LOOP_NAME:-OPTIMIZE_ROADMAP}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

WATCH=0
INTERVAL_SECONDS=5

while [[ $# -gt 0 ]]; do
  case "$1" in
    --watch)
      WATCH=1
      shift
      ;;
    --interval)
      INTERVAL_SECONDS="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

PID_FILE="${STATE_DIR}/${LOOP_NAME}/daemon.pid"
ACTIVE_LOG="${STATE_DIR}/${LOOP_NAME}/active.log"
LAST_MODE_FILE="${STATE_DIR}/${LOOP_NAME}/last_mode.txt"
ACTIVE_TASK="${STATE_DIR}/${LOOP_NAME}/active_task.json"
BLACKBOARD="${STATE_DIR}/${LOOP_NAME}/blackboard.json"

render() {
  echo "MOA Loop Monitor (DAG + Blackboard + PEFT)"
  echo "============================================"
  echo "loop_name      : ${LOOP_NAME}"
  echo "workspace      : ${WORKSPACE}"
  echo "time           : $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""

  # Daemon status
  if [[ -f "${PID_FILE}" ]]; then
    PID=$(cat "${PID_FILE}")
    if kill -0 "${PID}" 2>/dev/null; then
      echo "daemon_running : ✅ YES (PID ${PID})"
    else
      echo "daemon_running : ❌ DEAD (stale PID ${PID})"
    fi
  else
    echo "daemon_running : ⚠️  NOT STARTED"
  fi

  # Last mode
  if [[ -f "${LAST_MODE_FILE}" ]]; then
    echo "last_mode      : $(cat "${LAST_MODE_FILE}")"
  fi

  # Active task
  if [[ -f "${ACTIVE_TASK}" ]]; then
    echo ""
    echo "--- active_task.json ---"
    python3 -c "
import json, sys
d = json.load(open('${ACTIVE_TASK}'))
print(f\"  plan_id: {d.get('plan_id', 'N/A')}\")
print(f\"  task_id: {d.get('task_id', 'N/A')}\")
print(f\"  status: {d.get('status', 'N/A')}\")
print(f\"  epoch: {d.get('epoch', 0)}\")
print(f\"  frozen_backbone: {len(d.get('frozen_backbone', []))} items\")
print(f\"  adapters: {len(d.get('adapters', {}))} items\")
" 2>/dev/null || head -10 "${ACTIVE_TASK}"
  fi

  # Blackboard summary
  if [[ -f "${BLACKBOARD}" ]]; then
    echo ""
    echo "--- Blackboard ---"
    python3 -c "
import json, sys
sys.path.insert(0, '${SCRIPT_DIR}')
from core.shared_blackboard import SharedBlackboard
bb = SharedBlackboard(persist_path='${BLACKBOARD}')
print(bb.show_summary())
" 2>/dev/null || echo "  (unable to read blackboard)"
  fi

  # DAG + Iteration status
  echo ""
  echo "--- DAG & Iteration ---"
  python3 -c "
import json, sys
sys.path.insert(0, '${SCRIPT_DIR}')
from core.dag_scheduler import DAG, DAGScheduler
from core.iteration_manager import IterationManager

config = json.load(open('${SCRIPT_DIR}/config.json'))
dag = DAG.from_config(config.get('dag', {'nodes': []}))
scheduler = DAGScheduler(dag)
print(scheduler.visualize_ascii())

iter_mgr = IterationManager('${STATE_DIR}/${LOOP_NAME}/iterations', '${LOOP_NAME}')
print(iter_mgr.show_status())
" 2>/dev/null || echo "  (unable to read DAG/iteration state)"

  # Recent logs
  if [[ -L "${ACTIVE_LOG}" ]] || [[ -f "${ACTIVE_LOG}" ]]; then
    echo ""
    echo "--- recent activity ---"
    tail -15 "${ACTIVE_LOG}" 2>/dev/null || true
  fi

  echo ""
  echo "--- helpful commands ---"
  echo "start  : bash ${SCRIPT_DIR}/start_moa_loop.sh"
  echo "stop   : bash ${SCRIPT_DIR}/stop_moa_loop.sh"
  echo "status : bash ${SCRIPT_DIR}/status_moa_loop.sh"
  echo "logs   : tail -f ${ACTIVE_LOG}"
}

if [[ "${WATCH}" == "1" ]]; then
  while true; do
    clear
    render
    sleep "${INTERVAL_SECONDS}"
  done
else
  render
fi
