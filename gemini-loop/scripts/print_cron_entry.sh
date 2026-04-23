#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GEMINI_LOOP_WORKSPACE:-$PWD}"
START_CMD="cd ${WORKSPACE} && GEMINI_LOOP_WORKSPACE=${WORKSPACE} GEMINI_LOOP_LAUNCHER=tmux bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/start_daemon.sh"
STATUS_CMD="cd ${WORKSPACE} && GEMINI_LOOP_WORKSPACE=${WORKSPACE} bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/status_daemon.sh"

cat <<EOF
# Example cron entries for gemini-loop
#
# Start the daemon after reboot in a detached tmux session
@reboot ${START_CMD}
#
# Check every 5 minutes and start if not running (reference agent, fast health check)
*/5 * * * * ${STATUS_CMD} >/tmp/gemini-loop-status.log 2>&1 || ${START_CMD} >>/tmp/gemini-loop-status.log 2>&1
EOF
