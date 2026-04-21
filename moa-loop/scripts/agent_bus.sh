#!/usr/bin/env bash
#================================================================
# MOA Agent Message Bus
# Enables communication between agents in multi-agent workflows
#================================================================

BUS_DIR="${1:-.}"
mkdir -p "${BUS_DIR}"

# Message types
MSG_TYPE_TASK="task"
MSG_TYPE_RESULT="result"
MSG_TYPE_STATUS="status"
MSG_TYPE_QUERY="query"
MSG_TYPE_RESPONSE="response"

# Post a message
post_message() {
    local recipient="$1"
    local msg_type="$2"
    local content="$3"
    local sender="${4:-coordinator}"
    local timestamp=$(date +%s)

    local msg_file="${BUS_DIR}/${recipient}_inbox_${timestamp}.msg"

    cat > "$msg_file" <<EOF
FROM: ${sender}
TYPE: ${msg_type}
TIMESTAMP: ${timestamp}
---
${content}
EOF

    echo "Posted message to ${recipient}: ${msg_type}"
}

# Check inbox
check_inbox() {
    local agent="$1"
    local messages=($(ls "${BUS_DIR}/${agent}_inbox_"*.msg 2>/dev/null | sort))

    if [[ ${#messages[@]} -eq 0 ]]; then
        echo "No messages for ${agent}"
        return 1
    fi

    for msg in "${messages[@]}"; do
        echo "=== Message from ${msg} ==="
        cat "$msg"
        echo ""
        # Mark as read
        mv "$msg" "${msg}.read"
    done
}

# Query another agent
query_agent() {
    local target="$1"
    local query="$2"
    local sender="${3:-coordinator}"

    echo "Querying ${target}: ${query}"

    # Post query
    post_message "$target" "$MSG_TYPE_QUERY" "$query" "$sender"

    # Wait for response (with timeout)
    local timeout="${4:-30}"
    local start_time=$(date +%s)

    while true; do
        local response=($(ls "${BUS_DIR}/${sender}_inbox_"*.msg 2>/dev/null | head -1))

        if [[ -n "$response" ]]; then
            cat "$response"
            mv "$response" "${response}.read"
            return 0
        fi

        local elapsed=$(($(date +%s) - start_time))
        if [[ $elapsed -gt $timeout ]]; then
            echo "Timeout waiting for response from ${target}"
            return 1
        fi

        sleep 1
    done
}

# Broadcast to all agents
broadcast() {
    local msg_type="$1"
    local content="$2"
    local sender="${3:-coordinator}"
    local agents=("$@")
    unset agents[0] unset agents[1] unset agents[2]
    agents=("${agents[@]}")

    for agent in "${agents[@]}"; do
        post_message "$agent" "$msg_type" "$content" "$sender"
    done
}

# Execute command based on message
exec_message() {
    local msg_file="$1"

    local from=$(grep "^FROM:" "$msg_file" | sed 's/FROM: //')
    local type=$(grep "^TYPE:" "$msg_file" | sed 's/TYPE: //')
    local content=$(sed -n '/^---$/,$p' "$msg_file" | tail -n +2)

    case "$type" in
        "$MSG_TYPE_TASK")
            echo "Received task from ${from}: ${content}"
            # Execute task and post result back
            eval "$content" > /tmp/moa_result_$$.txt 2>&1
            post_message "$from" "$MSG_TYPE_RESULT" "$(cat /tmp/moa_result_$$.txt)" "self"
            ;;
        "$MSG_TYPE_QUERY")
            echo "Received query from ${from}: ${content}"
            # Process query and respond
            local response=$(eval "$content" 2>&1)
            post_message "$from" "$MSG_TYPE_RESPONSE" "$response" "self"
            ;;
        *)
            echo "Unknown message type: $type"
            ;;
    esac
}

case "$1" in
    post)
        post_message "$2" "$3" "$4" "${5:-coordinator}"
        ;;
    inbox|check)
        check_inbox "$2"
        ;;
    query)
        query_agent "$2" "$3" "${4:-coordinator}" "${5:-30}"
        ;;
    broadcast)
        shift; broadcast "$@"
        ;;
    exec)
        exec_message "$2"
        ;;
    *)
        echo "Usage: agent_bus.sh {post|inbox|query|broadcast|exec}"
        echo "  post <recipient> <type> <content> [sender]"
        echo "  inbox <agent>"
        echo "  query <target> <query> [sender] [timeout]"
        echo "  broadcast <type> <content> <sender> <agents...>"
        ;;
esac