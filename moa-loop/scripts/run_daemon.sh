#!/usr/bin/env bash
#================================================================
# MOA Loop v2.0 Daemon Entry Point
# Architecture: 纵向时序迭代 + 横向DAG协同 + 共享黑板 + PEFT
#================================================================

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOOP_NAME="${1:-OPTIMIZE_ROADMAP}"
INTERVAL="${INTERVAL:-60}"
WORKSPACE="${WORKSPACE:-$(pwd)}"

export LOOP_NAME INTERVAL WORKSPACE

# Run v2 daemon (DAG + Blackboard + PEFT)
python3 "${SKILL_DIR}/run_daemon.py"
