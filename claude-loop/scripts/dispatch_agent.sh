#!/usr/bin/env bash
#================================================================
# Claude Loop Dispatcher (Standalone - No Shared Templates)
#================================================================

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-}"
LOOP_NAME="${2:-DEFAULT_CLAUDE_ROADMAP}"
WORKSPACE="${WORKSPACE:-$(pwd)}"

export WORKSPACE LOOP_NAME MODE

STATE_DIR="${WORKSPACE}/.reflective-loop/state/${LOOP_NAME}"
LOG_DIR="${STATE_DIR}/dispatch_logs"
mkdir -p "${STATE_DIR}" "${LOG_DIR}"

dispatch_log="${LOG_DIR}/claude-dispatch_${LOOP_NAME}_$(date +%Y%m%d_%H%M%S).log"

log_dispatch() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [PROVIDER:claude] $1" | tee -a "${dispatch_log}"
}

build_prompt() {
    local mode="$1"
    local role
    case "$mode" in
        optimize) role="implementation" ;;
        check)    role="checker" ;;
    esac

    cat <<EOF
You are the AgentHUD ${role} agent for Claude Code.
Workspace: ${WORKSPACE}
Task: Follow .reflective-loop/state/${LOOP_NAME}/${LOOP_NAME}.md and update .reflective-loop/state/${LOOP_NAME}/sub-tasks/*.json.

CRITICAL INSTRUCTIONS:
1. Complete precisely one verifiable slice of work.
2. MANDATORY: git add and git commit your changes before finishing.
3. Update .reflective-loop/state/${LOOP_NAME}/${LOOP_NAME}.md with the latest status.
EOF
}

invoke_agent() {
    local model="$1"
    local prompt_file="$2"

    claude "$(cat "${prompt_file}")"
}

get_models() {
    echo "claude-sonnet-4-20250514
claude-haiku-4-20250514"
}

main() {
    local mode="${1:-optimize}"
    local loop="${2:-DEFAULT_CLAUDE_ROADMAP}"

    log_dispatch "=== Claude Dispatch Start ==="
    log_dispatch "Mode: ${mode}, Loop: ${loop}"

    local prompt_file="${STATE_DIR}/prompt_${mode}.txt"
    build_prompt "${mode}" > "${prompt_file}"
    log_dispatch "Prompt written to: ${prompt_file}"

    local success=false
    for model in $(get_models); do
        log_dispatch "Trying model: ${model}"
        if invoke_agent "${model}" "${prompt_file}" 2>&1 | tee -a "${dispatch_log}"; then
            success=true
            break
        else
            log_dispatch "Model ${model} failed, trying next..."
        fi
    done

    if $success; then
        log_dispatch "Dispatch completed successfully"
    else
        log_dispatch "ERROR: All models failed"
        exit 1
    fi
}

main "$@"