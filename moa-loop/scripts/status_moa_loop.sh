#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${MOA_LOOP_WORKSPACE:-$PWD}"
STATE_DIR="${MOA_LOOP_STATE_DIR:-${WORKSPACE}/.moa-loop/state}"
LOOP_NAME="${MOA_LOOP_LOOP_NAME:-OPTIMIZE_ROADMAP}"
PID_FILE="${STATE_DIR}/${LOOP_NAME}/daemon.pid"
ACTIVE_LOG="${STATE_DIR}/${LOOP_NAME}/active.log"
LAST_MODE_FILE="${STATE_DIR}/${LOOP_NAME}/last_mode.txt"
BLACKBOARD="${STATE_DIR}/${LOOP_NAME}/blackboard.json"

echo "=== MOA Loop Status: ${LOOP_NAME} ==="
echo "Workspace: ${WORKSPACE}"
echo "State Dir: ${STATE_DIR}/${LOOP_NAME}"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

if [[ -f "${PID_FILE}" ]]; then
    PID=$(cat "${PID_FILE}")
    if kill -0 "${PID}" 2>/dev/null; then
        echo "✅ Daemon RUNNING (PID ${PID})"
    else
        echo "❌ Daemon DEAD (stale PID ${PID})"
        rm -f "${PID_FILE}"
        exit 1
    fi
else
    echo "⚠️  No PID file found - daemon not started"
    exit 1
fi

# Show last mode
if [[ -f "${LAST_MODE_FILE}" ]]; then
    echo "Last Mode: $(cat "${LAST_MODE_FILE}")"
fi

# Show blackboard summary
if [[ -f "${BLACKBOARD}" ]]; then
    AGENT_COUNT=$(python3 -c "import json; d=json.load(open('${BLACKBOARD}')); print(len(d.get('agents',{})))" 2>/dev/null || echo "0")
    KNOWLEDGE_COUNT=$(python3 -c "import json; d=json.load(open('${BLACKBOARD}')); print(len(d.get('knowledge',{})))" 2>/dev/null || echo "0")
    echo "Blackboard: ${KNOWLEDGE_COUNT} knowledge entries, ${AGENT_COUNT} agents"
fi

# Show recent activity
if [[ -L "${ACTIVE_LOG}" ]] || [[ -f "${ACTIVE_LOG}" ]]; then
    echo ""
    echo "Recent activity:"
    tail -10 "${ACTIVE_LOG}" 2>/dev/null || true
fi
