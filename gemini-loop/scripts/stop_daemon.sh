#!/usr/bin/env bash
#================================================================
# Gemini Loop - Stop daemon gracefully
#================================================================
set -euo pipefail

WORKSPACE="${GEMINI_LOOP_WORKSPACE:-$PWD}"
STATE_DIR="${GEMINI_LOOP_STATE_DIR:-${WORKSPACE}/.reflective-loop/state}"
LOOP_NAME="${GEMINI_LOOP_LOOP_NAME:-OPTIMIZE_ROADMAP}"
PID_FILE="${STATE_DIR}/${LOOP_NAME}/daemon.pid"

echo "=== Stopping Gemini Loop: ${LOOP_NAME} ==="

if [[ ! -f "${PID_FILE}" ]]; then
    echo "gemini-loop daemon is not running (no PID file)"
    exit 0
fi

PID="$(cat "${PID_FILE}")"

if kill -0 "${PID}" 2>/dev/null; then
    kill "${PID}"
    echo "Sent SIGTERM to PID ${PID}"
    for i in $(seq 1 5); do
        if ! kill -0 "${PID}" 2>/dev/null; then
            break
        fi
        sleep 1
    done
    if kill -0 "${PID}" 2>/dev/null; then
        kill -9 "${PID}" 2>/dev/null || true
        echo "Force killed PID ${PID}"
    fi
else
    echo "Stale PID file found, cleaning up"
fi

rm -f "${PID_FILE}"
echo "Daemon stopped"
