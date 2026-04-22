#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${CLAUDE_LOOP_WORKSPACE:-$PWD}"
START_CMD="cd ${WORKSPACE} && CLAUDE_LOOP_WORKSPACE=${WORKSPACE} CLAUDE_LOOP_LAUNCHER=tmux bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/start_claude_loop.sh"
STATUS_CMD="cd ${WORKSPACE} && CLAUDE_LOOP_WORKSPACE=${WORKSPACE} bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/status_claude_loop.sh"

cat <<EOF
# Example cron entries for claude-loop
#
# Start the daemon after reboot in a detached tmux session
@reboot ${START_CMD}
#
# Check every 10 minutes and start if not running
*/10 * * * * ${STATUS_CMD} >/tmp/claude-loop-status.log 2>&1 || ${START_CMD} >>/tmp/claude-loop-status.log 2>&1
EOF
