#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${MOA_LOOP_WORKSPACE:-$PWD}"
START_CMD="cd ${WORKSPACE} && MOA_LOOP_WORKSPACE=${WORKSPACE} MOA_LOOP_LAUNCHER=tmux bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/start_moa_loop.sh"
STATUS_CMD="cd ${WORKSPACE} && MOA_LOOP_WORKSPACE=${WORKSPACE} bash $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/status_moa_loop.sh"

cat <<EOF
# Example cron entries for moa-loop
#
# Start the daemon after reboot in a detached tmux session
@reboot ${START_CMD}
#
# Check every 5 minutes and start if not running (multi-agent orchestration, frequent health check)
*/5 * * * * ${STATUS_CMD} >/tmp/moa-loop-status.log 2>&1 || ${START_CMD} >>/tmp/moa-loop-status.log 2>&1
EOF
