#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${QWEN_LOOP_WORKSPACE:-$PWD}"
START_CMD="cd ${WORKSPACE} && QWEN_LOOP_WORKSPACE=${WORKSPACE} QWEN_LOOP_LAUNCHER=tmux bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/start_qwen_loop.sh"
STATUS_CMD="cd ${WORKSPACE} && QWEN_LOOP_WORKSPACE=${WORKSPACE} bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/status_qwen_loop.sh"

cat <<EOF
# Example cron entries for qwen-loop
#
# Start the daemon after reboot in a detached tmux session
@reboot ${START_CMD}
#
# Check every 10 minutes and start if not running
*/10 * * * * ${STATUS_CMD} >/tmp/qwen-loop-status.log 2>&1 || ${START_CMD} >>/tmp/qwen-loop-status.log 2>&1
EOF
