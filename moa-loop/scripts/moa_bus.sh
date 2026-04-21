#!/usr/bin/env bash
#================================================================
# MOA Bus Shell Wrapper
# FIFO + SQLite Hybrid Communication System
#================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOA_BUS="${SCRIPT_DIR}/moa_bus.py"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

usage() {
    cat <<EOF
╔════════════════════════════════════════════════════════════════╗
║                    MOA Bus CLI                                ║
╚════════════════════════════════════════════════════════════════╝

Usage: moa_bus.sh <command> [args...]

📨 Messages:
   moa_bus.sh post <to> <type> <content>     Post message to agent
   moa_bus.sh recv <agent> [timeout]         Receive message from FIFO
   moa_bus.sh broadcast <type> <content>      Broadcast to all agents

🤖 Agents:
   moa_bus.sh register <name> <caps...>      Register agent
   moa_bus.sh agents                         List active agents
   moa_bus.sh heartbeat <name>               Send heartbeat

📚 Knowledge:
   moa_bus.sh knowledge add <key> <value>   Add knowledge
   moa_bus.sh knowledge query <key>         Query knowledge
   moa_bus.sh knowledge list                List all knowledge

📋 Tasks:
   moa_bus.sh task create <id> <desc> <to>  Create task
   moa_bus.sh task update <id> <status>    Update task
   moa_bus.sh task list [status]           List tasks
   moa_bus.sh task get <id>                Get task details

💾 State:
   moa_bus.sh state set <key> <value>      Set state
   moa_bus.sh state get <key>              Get state

🔍 Query:
   moa_bus.sh query <sql>                  Custom SQL query
   moa_bus.sh summary                       Show bus summary

EOF
}

case "$1" in
    post)
        python3 "$MOA_BUS" post "$2" "$3" "$4"
        ;;
    recv)
        python3 "$MOA_BUS" recv "$2" "${3:-1}"
        ;;
    broadcast)
        python3 "$MOA_BUS" broadcast "$2" "$3"
        ;;
    register)
        shift
        python3 "$MOA_BUS" register "$@"
        ;;
    agents)
        python3 "$MOA_BUS" agents
        ;;
    heartbeat)
        python3 "$MOA_BUS" heartbeat "$2"
        ;;
    knowledge)
        shift
        python3 "$MOA_BUS" knowledge "$@"
        ;;
    task)
        shift
        python3 "$MOA_BUS" task "$@"
        ;;
    state)
        shift
        python3 "$MOA_BUS" state "$@"
        ;;
    query)
        shift
        python3 "$MOA_BUS" query "$*"
        ;;
    summary)
        python3 "$MOA_BUS" summary
        ;;
    init)
        python3 "$MOA_BUS" init
        ;;
    *)
        usage
        ;;
esac