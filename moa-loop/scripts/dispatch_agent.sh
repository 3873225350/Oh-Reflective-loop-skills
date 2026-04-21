#!/usr/bin/env bash
#================================================================
# MOA Loop Dispatcher v2.0 (Mixture of Agents)
# Enhanced with task routing, parallel execution, and result aggregation
#================================================================

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="${SKILL_DIR}/scripts"
MODE="${1:-}"
LOOP_NAME="${2:-DEFAULT_MOA_ROADMAP}"
WORKSPACE="${WORKSPACE:-$(pwd)}"
CONFIG_FILE="${SCRIPT_DIR}/config.json"

export WORKSPACE LOOP_NAME MODE

STATE_DIR="${WORKSPACE}/.reflective-loop/state/${LOOP_NAME}"
LOG_DIR="${STATE_DIR}/dispatch_logs"
mkdir -p "${STATE_DIR}" "${LOG_DIR}"

dispatch_log="${LOG_DIR}/moa-dispatch_${LOOP_NAME}_$(date +%Y%m%d_%H%M%S).log"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_dispatch() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [${BLUE}PROVIDER:moa${NC}] $1" | tee -a "${dispatch_log}"
}

log_success() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [${GREEN}SUCCESS${NC}] $1" | tee -a "${dispatch_log}"
}

log_error() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [${RED}ERROR${NC}] $1" | tee -a "${dispatch_log}"
}

log_warn() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [${YELLOW}WARN${NC}] $1" | tee -a "${dispatch_log}"
}

# Get JSON value (simple parser)
get_json_value() {
    local key="$1"
    local file="$2"
    grep "\"$key\"" "$file" | head -1 | sed 's/.*: *"\([^"]*\)".*/\1/' | tr -d ' '
}

# Get array from JSON
get_json_array() {
    local key="$1"
    local file="$2"
    grep -A10 "\"$key\"" "$file" | grep '"' | sed 's/.*"\([^"]*\)".*/\1/' | tr -d ',"' | tr ',' ' '
}

# Detect available agents
detect_available_agents() {
    local available=()

    for entry in gemini:gemini claude:claude qwen:qwen kimi:kimi cursor:cursor minimax:mmx; do
        agent="${entry%%:*}"
        cmd="${entry##*:}"

        if command -v "$cmd" &>/dev/null; then
            available+=("$agent")
        fi
    done

    echo "${available[@]}"
}

# Get enabled agents from config
get_enabled_agents() {
    if [[ -f "$CONFIG_FILE" ]]; then
        get_json_array "enabled_agents" "$CONFIG_FILE"
    else
        echo "gemini claude qwen kimi"
    fi
}

# Get primary agent
get_primary_agent() {
    if [[ -f "$CONFIG_FILE" ]]; then
        local primary=$(get_json_value "primary_agent" "$CONFIG_FILE")
        if [[ -n "$primary" ]]; then
            echo "$primary"
            return
        fi
    fi
    local available=($(detect_available_agents))
    echo "${available[0]:-gemini}"
}

# Get max parallel
get_max_parallel() {
    if [[ -f "$CONFIG_FILE" ]]; then
        local max=$(grep "max_parallel" "$CONFIG_FILE" | sed 's/.*: *\([0-9]*\).*/\1/')
        echo "${max:-2}"
    else
        echo "2"
    fi
}

# Check if agent is available
is_agent_available() {
    local agent="$1"
    local cmd=""

    case "$agent" in
        gemini) cmd="gemini" ;;
        claude) cmd="claude" ;;
        qwen) cmd="qwen" ;;
        kimi) cmd="kimi" ;;
        cursor) cmd="cursor" ;;
        minimax) cmd="mmx" ;;
    esac

    command -v "$cmd" &>/dev/null
}

# Get agent capability info
get_agent_info() {
    local agent="$1"
    if [[ -f "$CONFIG_FILE" ]]; then
        grep -A8 "\"$agent\"" "$CONFIG_FILE" 2>/dev/null | head -7
    fi
}

# Route task to best agent based on task type
route_task() {
    local task_type="${1:-default}"

    if [[ -f "$CONFIG_FILE" ]] && grep -q "task_routing" "$CONFIG_FILE"; then
        local agents=$(get_json_array "$task_type" "$CONFIG_FILE")
        if [[ -n "$agents" ]]; then
            echo "$agents"
            return
        fi
    fi

    echo "gemini claude"
}

# Invoke single agent
invoke_single_agent() {
    local agent="$1"
    local prompt_file="$2"
    local agent_log="${LOG_DIR}/${agent}-${LOOP_NAME}_$(date +%Y%m%d_%H%M%S).log"

    log_dispatch "▶ Invoking ${agent}..."

    local start_time=$(date +%s)
    local result=0

    case "$agent" in
        gemini)
            gemini --resume latest --approval-mode yolo --output-format text "$(cat "${prompt_file}")" 2>&1 | tee -a "$agent_log"
            result=${PIPESTATUS[0]}
            ;;
        claude)
            claude "$(cat "${prompt_file}")" 2>&1 | tee -a "$agent_log"
            result=$?
            ;;
        qwen)
            qwen -c -p "$(cat "${prompt_file}")" 2>&1 | tee -a "$agent_log"
            result=$?
            ;;
        kimi)
            kimi -c -p "$(cat "${prompt_file}")" 2>&1 | tee -a "$agent_log"
            result=$?
            ;;
        cursor)
            cursor "$(cat "${prompt_file}")" 2>&1 | tee -a "$agent_log"
            result=$?
            ;;
        minimax)
            mmx text chat --non-interactive --quiet --output text --message "$(cat "${prompt_file}")" 2>&1 | tee -a "$agent_log"
            result=$?
            ;;
        *)
            log_error "Unknown agent: $agent"
            return 1
            ;;
    esac

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [[ $result -eq 0 ]]; then
        log_success "✓ ${agent} completed in ${duration}s"
        return 0
    else
        log_error "✗ ${agent} failed (exit code: $result) in ${duration}s"
        return $result
    fi
}

# Parallel execution
run_parallel() {
    local agents=("$@")
    local prompt_file="$1"
    local pids=()
    local results=()

    log_dispatch "▶ Starting parallel execution with ${#agents[@]} agents..."

    for agent in "${agents[@]}"; do
        if is_agent_available "$agent"; then
            invoke_single_agent "$agent" "$prompt_file" &
            pids+=($!)
            results+=("pending")
        else
            log_warn "Agent $agent not available, skipping"
        fi
    done

    # Wait for all and collect results
    local all_success=true
    for i in "${!pids[@]}"; do
        if wait "${pids[$i]}"; then
            results[$i]="success"
        else
            results[$i]="failed"
            all_success=false
        fi
    done

    if $all_success; then
        log_success "All ${#agents[@]} agents completed successfully"
        return 0
    else
        log_warn "Some agents failed"
        return 1
    fi
}

# Build prompt with agent awareness
build_prompt() {
    local mode="$1"
    local role
    case "$mode" in
        optimize) role="implementation" ;;
        check)    role="checker" ;;
    esac

    local available=($(detect_available_agents))
    local enabled=($(get_enabled_agents))
    local primary=$(get_primary_agent)
    local max_parallel=$(get_max_parallel)
    local available_str=$(IFS=,; echo "${available[*]}")

    # Filter to only enabled and available agents
    local usable_agents=()
    for agent in "${enabled[@]}"; do
        if is_agent_available "$agent"; then
            usable_agents+=("$agent")
        fi
    done
    local usable_str=$(IFS=,; echo "${usable_agents[*]}")

    cat <<EOF
You are the MOA (Mixture of Agents) ${role} agent orchestrator.
Workspace: ${WORKSPACE}
Task: Follow .reflective-loop/state/${LOOP_NAME}/${LOOP_NAME}.md and update .reflective-loop/state/${LOOP_NAME}/sub-tasks/*.json.

## Agent Configuration
- Available Agents: ${available_str}
- Enabled Agents: ${usable_str}
- Primary Agent: ${primary}
- Max Parallel: ${max_parallel}

## Available Agent Capabilities
$(for agent in "${usable_agents[@]}"; do echo "- ${agent}: $(get_agent_info "$agent" | head -2)"; done)

## CRITICAL INSTRUCTIONS
1. Complete precisely one verifiable slice of work.
2. MANDATORY: git add and git commit your changes before finishing.
3. Update .reflective-loop/state/${LOOP_NAME}/${LOOP_NAME}.md with the latest status.
4. You may coordinate multiple agents if needed for complex tasks.
5. Use parallel execution for independent sub-tasks.
EOF
}

main() {
    local mode="${1:-optimize}"
    local loop="${2:-DEFAULT_MOA_ROADMAP}"

    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  MOA (Mixture of Agents) Dispatcher v2.0                     ║"
    echo "╚════════════════════════════════════════════════════════════════╝"

    log_dispatch "══════════ MOA Dispatch Start ══════════"
    log_dispatch "Mode: ${mode}, Loop: ${loop}"

    # Detect and report agent status
    local available=($(detect_available_agents))
    local enabled=($(get_enabled_agents))
    local primary=$(get_primary_agent)
    local max_parallel=$(get_max_parallel)

    echo ""
    log_dispatch "📊 Agent Status:"
    log_dispatch "   Available: ${available[*]}"
    log_dispatch "   Enabled: ${enabled[*]}"
    log_dispatch "   Primary: ${primary}"
    log_dispatch "   Max Parallel: ${max_parallel}"
    echo ""

    # Build prompt
    local prompt_file="${STATE_DIR}/prompt_${mode}_moa.txt"
    build_prompt "${mode}" > "${prompt_file}"
    log_dispatch "📝 Prompt written to: ${prompt_file}"

    # Try primary agent with fallback chain
    local fallback_chain=()
    for agent in "${enabled[@]}"; do
        if [[ "$agent" != "$primary" ]] && is_agent_available "$agent"; then
            fallback_chain+=("$agent")
        fi
    done

    local success=false

    # Try primary agent first
    if is_agent_available "$primary"; then
        log_dispatch "🚀 Trying primary agent: ${primary}"
        if invoke_single_agent "$primary" "$prompt_file"; then
            success=true
        fi
    fi

    # Fallback chain
    if ! $success; then
        log_warn "Primary agent failed, trying fallback chain..."
        for agent in "${fallback_chain[@]}"; do
            if is_agent_available "$agent"; then
                log_dispatch "🔄 Trying fallback: ${agent}"
                if invoke_single_agent "$agent" "$prompt_file"; then
                    success=true
                    break
                fi
            fi
        done
    fi

    echo ""
    if $success; then
        log_success "══════════ Dispatch Complete ══════════"
        exit 0
    else
        log_error "══════════ All Agents Failed ══════════"
        exit 1
    fi
}

main "$@"