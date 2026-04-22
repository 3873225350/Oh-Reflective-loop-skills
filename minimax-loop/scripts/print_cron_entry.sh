#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${MINIMAX_LOOP_WORKSPACE:-$PWD}"
START_CMD="cd ${WORKSPACE} && MINIMAX_LOOP_WORKSPACE=${WORKSPACE} MINIMAX_LOOP_LAUNCHER=tmux bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/start_minimax_loop.sh"
STATUS_CMD="cd ${WORKSPACE} && MINIMAX_LOOP_WORKSPACE=${WORKSPACE} bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/status_minimax_loop.sh"

cat <<EOF
# Example cron entries for minimax-loop
#
# Start the daemon after reboot in a detached tmux session
@reboot ${START_CMD}
#
# Check every 5 minutes and start if not running (lightweight agent, fast health check)
*/5 * * * * ${STATUS_CMD} >/tmp/minimax-loop-status.log 2>&1 || ${START_CMD} >>/tmp/minimax-loop-status.log 2>&1
EOF
