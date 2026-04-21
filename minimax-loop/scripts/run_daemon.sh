#!/usr/bin/env bash
#================================================================
# Gemini Loop Daemon (Using Shared Templates)
#================================================================

# Get skill directory
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHARED_DIR="/home/clashuser/hzh/work_bo/agent_ui/agent_hud/Reflective-loop/shared-templates"

# Parameters
LOOP_NAME="${1:-UI_PERF_ROADMAP}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-60}"
WORKSPACE="${WORKSPACE:-$(pwd)}"

export WORKSPACE LOOP_NAME INTERVAL_SECONDS

# Source shared daemon framework
source "${SHARED_DIR}/daemon_framework.sh"

#================================================================
# Gemini-specific implementations
#================================================================

# Invoke gemini dispatch
invoke_dispatch() {
    local mode="$1"
    local loop="$2"
    bash "${SKILL_DIR}/scripts/dispatch_agent.sh" "$mode" "$loop"
}

# Run shared daemon
main "$@"