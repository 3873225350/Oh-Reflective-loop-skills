#!/usr/bin/env bash
#================================================================
# Gemini Loop - Start Daemon in background (for cron/systemd)
#================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${GEMINI_LOOP_WORKSPACE:-$PWD}"
STATE_DIR="${GEMINI_LOOP_STATE_DIR:-${WORKSPACE}/.reflective-loop/state}"
LOOP_NAME="${GEMINI_LOOP_LOOP_NAME:-${1:-OPTIMIZE_ROADMAP}}"
INTERVAL="${GEMINI_LOOP_INTERVAL:-60}"
PID_FILE="${STATE_DIR}/${LOOP_NAME}/daemon.pid"
LOG_DIR="${STATE_DIR}/${LOOP_NAME}/logs"

mkdir -p "${LOG_DIR}"

# Check if already running
if [[ -f "${PID_FILE}" ]]; then
    EXISTING_PID="$(cat "${PID_FILE}" 2>/dev/null || true)"
    if [[ -n "${EXISTING_PID}" ]] && kill -0 "${EXISTING_PID}" 2>/dev/null; then
        echo "gemini-loop daemon is already running with PID ${EXISTING_PID}"
        exit 0
    fi
    echo "Stale PID file found, cleaning up"
    rm -f "${PID_FILE}"
fi

echo "Starting gemini-loop daemon for ${LOOP_NAME} (interval=${INTERVAL}s)"

# Determine launcher (tmux preferred, nohup fallback)
LAUNCHER="${GEMINI_LOOP_LAUNCHER:-auto}"
if [[ "${LAUNCHER}" == "auto" ]]; then
    if command -v tmux >/dev/null 2>&1; then
        LAUNCHER="tmux"
    else
        LAUNCHER="nohup"
    fi
fi

SESSION_NAME="gemini-loop-${LOOP_NAME}-$(printf '%s' "${WORKSPACE}" | md5sum | cut -c1-8)"

if [[ "${LAUNCHER}" == "tmux" ]]; then
    if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
        echo "gemini-loop tmux session already exists: ${SESSION_NAME}"
        exit 0
    fi
    tmux new-session -d -s "${SESSION_NAME}" \
        "cd '${WORKSPACE}' && WORKSPACE='${WORKSPACE}' LOOP_NAME='${LOOP_NAME}' INTERVAL='${INTERVAL}' bash '${SCRIPT_DIR}/run_daemon.sh' '${LOOP_NAME}' >> '${LOG_DIR}/daemon-$(date +%Y%m%d).log' 2>&1"
    echo "Started gemini-loop in tmux session: ${SESSION_NAME}"
else
    nohup env \
        WORKSPACE="${WORKSPACE}" \
        LOOP_NAME="${LOOP_NAME}" \
        INTERVAL="${INTERVAL}" \
        bash "${SCRIPT_DIR}/run_daemon.sh" "${LOOP_NAME}" \
        >> "${LOG_DIR}/daemon-$(date +%Y%m%d).log" 2>&1 &
    NEW_PID=$!
    echo "${NEW_PID}" > "${PID_FILE}"
    echo "Started gemini-loop daemon (PID ${NEW_PID})"
fi
