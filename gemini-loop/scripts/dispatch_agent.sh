#!/usr/bin/env bash
#================================================================
# Gemini Loop Dispatcher (Standalone - No Shared Templates)
#================================================================

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-}"
LOOP_NAME="${2:-DEFAULT_GEMINI_ROADMAP}"
WORKSPACE="${WORKSPACE:-$(pwd)}"

export WORKSPACE LOOP_NAME MODE

STATE_DIR="${WORKSPACE}/.reflective-loop/state/${LOOP_NAME}"
LOG_DIR="${STATE_DIR}/dispatch_logs"
mkdir -p "${STATE_DIR}" "${LOG_DIR}"

dispatch_log="${LOG_DIR}/gemini-dispatch_${LOOP_NAME}_$(date +%Y%m%d_%H%M%S).log"

log_dispatch() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [PROVIDER:gemini] $1" | tee -a "${dispatch_log}"
}

build_prompt() {
    local mode="$1"
    local role
    case "$mode" in
        optimize) role="implementation" ;;
        check)    role="checker" ;;
    esac

    cat <<EOF
You are the AgentHUD ${role} agent for Gemini.
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

    # Use PIPESTATUS to capture gemini's actual exit code (not tee's)
    gemini --model "${model}" --resume latest --approval-mode yolo --output-format text "$(cat "${prompt_file}")" 2>&1 | tee -a "${dispatch_log}"
    return ${PIPESTATUS[0]}
}

get_models() {
    # Ordered by availability/throughput - flash models have more capacity
    echo "gemini-2.5-flash
gemini-3.1-flash-lite-preview
gemini-2.5-pro
gemini-3.1-pro-preview
gemini-3-flash-preview"
}

main() {
    local mode="${1:-optimize}"
    local loop="${2:-DEFAULT_GEMINI_ROADMAP}"

    log_dispatch "=== Gemini Dispatch Start ==="
    log_dispatch "Mode: ${mode}, Loop: ${loop}"

    local prompt_file="${STATE_DIR}/prompt_${mode}.txt"
    build_prompt "${mode}" > "${prompt_file}"
    log_dispatch "Prompt written to: ${prompt_file}"

    local success=false
    for model in $(get_models); do
        log_dispatch "Trying model: ${model}"
        if invoke_agent "${model}" "${prompt_file}"; then
            success=true
            log_dispatch "Model ${model} succeeded"
            break
        else
            local exit_code=$?
            log_dispatch "Model ${model} failed (exit=${exit_code}), trying next..."
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
