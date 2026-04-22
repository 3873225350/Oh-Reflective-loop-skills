#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${CURSOR_LOOP_WORKSPACE:-$PWD}"
START_CMD="cd ${WORKSPACE} && CURSOR_LOOP_WORKSPACE=${WORKSPACE} CURSOR_LOOP_LAUNCHER=tmux bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/start_cursor_loop.sh"
STATUS_CMD="cd ${WORKSPACE} && CURSOR_LOOP_WORKSPACE=${WORKSPACE} bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/status_cursor_loop.sh"

cat <<EOF
# Example cron entries for cursor-loop
#
# Start the daemon after reboot in a detached tmux session
@reboot ${START_CMD}
#
# Check every 15 minutes and start if not running
*/15 * * * * ${STATUS_CMD} >/tmp/cursor-loop-status.log 2>&1 || ${START_CMD} >>/tmp/cursor-loop-status.log 2>&1
EOF
