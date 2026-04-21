#!/usr/bin/env bash
#================================================================
# MOA Agent Detection Script
# Detects which AI agents are available in the system
#================================================================

detect_agent() {
    local agent="$1"
    local cmd="$2"

    if command -v "$cmd" &>/dev/null; then
        echo "  {\"$agent\": \"available\"}"
        return 0
    else
        echo "  {\"$agent\": \"unavailable\"}"
        return 1
    fi
}

echo "🔍 Detecting available AI agents..."

AGENTS=(
    "gemini:gemini"
    "claude:claude"
    "qwen:qwen"
    "kimi:kimi"
    "cursor:cursor"
    "minimax:mmx"
)

AVAILABLE=()
UNAVAILABLE=()

for entry in "${AGENTS[@]}"; do
    agent="${entry%%:*}"
    cmd="${entry##*:}"

    if command -v "$cmd" &>/dev/null; then
        AVAILABLE+=("$agent")
        echo "✅ $agent is available"
    else
        UNAVAILABLE+=("$agent")
        echo "❌ $agent is not available"
    fi
done

echo ""
echo "📊 Summary:"
echo "   Available: ${AVAILABLE[*]}"
echo "   Unavailable: ${UNAVAILABLE[*]}"
echo ""

# Output JSON for use by other scripts
echo "{"
echo "  \"available\": [$(IFS=,; echo "${AVAILABLE[*]}")],"
echo "  \"unavailable\": [$(IFS=,; echo "${UNAVAILABLE[*]}")],"
echo "  \"primary_agent\": \"${AVAILABLE[0]:-gemini}\""
echo "}"