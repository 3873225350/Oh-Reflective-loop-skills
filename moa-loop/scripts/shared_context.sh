#!/usr/bin/env bash
#================================================================
# MOA Shared Context Manager
# Manages shared state and context between agents
#================================================================

# Use fixed default directory, can be overridden by MOA_CONTEXT_DIR env var
CONTEXT_DIR="${MOA_CONTEXT_DIR:-.moa_context}"
mkdir -p "${CONTEXT_DIR}"

# Context files
CONTEXT_FILE="${CONTEXT_DIR}/shared_context.json"
TASK_QUEUE="${CONTEXT_DIR}/task_queue.json"
AGENT_REGISTRY="${CONTEXT_DIR}/agent_registry.json"
LOCK_FILE="${CONTEXT_DIR}/.lock"

# Initialize context
init_context() {
    cat > "$CONTEXT_FILE" <<'EOF'
{
  "initialized_at": "TIMESTAMP",
  "last_update": "TIMESTAMP",
  "shared_knowledge": {},
  "task_results": {},
  "global_state": {},
  "logs": []
}
EOF
    sed -i "s/TIMESTAMP/$(date -Iseconds)/g" "$CONTEXT_FILE"
    echo "Context initialized at ${CONTEXT_DIR}"
}

# Lock for atomic operations
lock() {
    mkdir "$LOCK_FILE" 2>/dev/null
}

unlock() {
    rmdir "$LOCK_FILE" 2>/dev/null
}

# Add to shared knowledge
add_knowledge() {
    local key="$1"
    local value="$2"
    local agent="${3:-unknown}"

    lock
    local temp=$(mktemp)

    jq --arg key "$key" --arg value "$value" --arg agent "$agent" \
       --arg timestamp "$(date -Iseconds)" \
       '.shared_knowledge[$key] = {
            value: $value,
            added_by: $agent,
            timestamp: $timestamp
         } | .last_update = $timestamp' \
       "$CONTEXT_FILE" > "$temp" && mv "$temp" "$CONTEXT_FILE"

    echo "Added knowledge: ${key} (by ${agent})"
    unlock
}

# Query shared knowledge
query_knowledge() {
    local key="$1"

    jq -r ".shared_knowledge.\"$key\".value // empty" "$CONTEXT_FILE"
}

# List all knowledge
list_knowledge() {
    jq -r '.shared_knowledge | to_entries[] | "\(.key): \(.value.value) [by \(.value.added_by)]"' "$CONTEXT_FILE"
}

# Store task result
store_result() {
    local task_id="$1"
    local result="$2"
    local agent="${3:-unknown}"
    local status="${4:-completed}"

    lock
    local temp=$(mktemp)

    jq --arg task_id "$task_id" --arg result "$result" \
       --arg agent "$agent" --arg status "$status" \
       --arg timestamp "$(date -Iseconds)" \
       '.task_results[$task_id] = {
            result: $result,
            completed_by: $agent,
            status: $status,
            timestamp: $timestamp
         } | .last_update = $timestamp' \
       "$CONTEXT_FILE" > "$temp" && mv "$temp" "$CONTEXT_FILE"

    echo "Stored result for task: ${task_id}"
    unlock
}

# Get task result
get_result() {
    local task_id="$1"

    jq -r ".task_results.\"$task_id\".result // empty" "$CONTEXT_FILE"
}

# Register agent
register_agent() {
    local agent_name="$1"
    local capabilities="$2"
    local status="${3:-active}"

    lock
    local temp=$(mktemp)

    jq --arg name "$agent_name" --arg caps "$capabilities" \
       --arg status "$status" \
       --arg timestamp "$(date -Iseconds)" \
       '.agent_registry[$name] = {
            capabilities: ($caps | split(",")),
            status: $status,
            registered_at: $timestamp,
            last_seen: $timestamp
         }' \
       "$CONTEXT_FILE" > "$temp" && mv "$temp" "$CONTEXT_FILE"

    echo "Registered agent: ${agent_name} (${capabilities})"
    unlock
}

# Update agent heartbeat
heartbeat() {
    local agent_name="$1"

    lock
    local temp=$(mktemp)

    jq --arg name "$agent_name" \
       --arg timestamp "$(date -Iseconds)" \
       '.agent_registry[$name].last_seen = $timestamp' \
       "$CONTEXT_FILE" > "$temp" && mv "$temp" "$CONTEXT_FILE"

    unlock
}

# List active agents
list_agents() {
    local timeout="${1:-60}"
    local now=$(date +%s)
    local cutoff=$((now - timeout))

    jq -r --arg cutoff "$cutoff" \
       '.agent_registry | to_entries[] |
        select(.value.status == "active") |
        "\(.key): \(.value.capabilities | join(", "))"' \
       "$CONTEXT_FILE" 2>/dev/null || echo "No active agents"
}

# Update global state
set_state() {
    local key="$1"
    local value="$2"

    lock
    local temp=$(mktemp)

    jq --arg key "$key" --arg value "$value" \
       '.global_state[$key] = $value | .last_update = (now | strftime("%Y-%m-%dT%H:%M:%S"))' \
       "$CONTEXT_FILE" > "$temp" && mv "$temp" "$CONTEXT_FILE"

    echo "Set state: ${key} = ${value}"
    unlock
}

# Get global state
get_state() {
    local key="$1"

    jq -r ".global_state.\"$key\" // empty" "$CONTEXT_FILE"
}

# Add log entry
log_event() {
    local level="$1"
    local message="$2"
    local agent="${3:-system}"

    lock
    local temp=$(mktemp)

    jq --arg level "$level" --arg msg "$message" \
       --arg agent "$agent" --arg ts "$(date -Iseconds)" \
       '.logs += [{
            level: $level,
            message: $msg,
            agent: $agent,
            timestamp: $ts
         }] | .last_update = $ts' \
       "$CONTEXT_FILE" > "$temp" && mv "$temp" "$CONTEXT_FILE"

    unlock
}

# Show context summary
summary() {
    echo "=== MOA Shared Context Summary ==="
    echo ""
    echo "Directory: ${CONTEXT_DIR}"
    echo ""
    echo "Active Agents:"
    list_agents
    echo ""
    echo "Shared Knowledge:"
    list_knowledge
    echo ""
    echo "Global State:"
    jq -r '.global_state | to_entries[] | "  \(.key): \(.value)"' "$CONTEXT_FILE"
}

case "$1" in
    init)
        init_context
        ;;
    add)
        add_knowledge "$2" "$3" "${4:-unknown}"
        ;;
    query)
        query_knowledge "$2"
        ;;
    list)
        list_knowledge
        ;;
    result)
        case "$2" in
            store) store_result "$3" "$4" "${5:-unknown}" "${6:-completed}" ;;
            get) get_result "$3" ;;
        esac
        ;;
    agent)
        case "$2" in
            register) register_agent "$3" "$4" "${5:-active}" ;;
            list) list_agents "${3:-60}" ;;
            heartbeat) heartbeat "$3" ;;
        esac
        ;;
    state)
        case "$2" in
            set) set_state "$3" "$4" ;;
            get) get_state "$3" ;;
        esac
        ;;
    log)
        log_event "$2" "$3" "${4:-system}"
        ;;
    summary)
        summary
        ;;
    *)
        echo "Usage: shared_context.sh {init|add|query|list|result|agent|state|log|summary}"
        ;;
esac