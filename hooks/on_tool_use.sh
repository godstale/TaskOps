#!/bin/bash
# Hook: Called after tool use (Edit, Write, Bash)
# TaskOps Hook: 도구 사용 후 진행 상황 기록
# Triggered by PostToolUse hook in Claude Code
#
# Safety: Only fires when TaskOps is the active tracking system.
# Set TASKOPS_ACTIVE=1 when TaskOps is chosen at the Planning Gate.
# This prevents conflicts with other execution tracking skills
# (e.g., executing-plans, subagent-driven-development) that use
# TodoWrite-based tracking.

# Guard: skip if TaskOps is not the active tracking system
if [ "${TASKOPS_ACTIVE}" != "1" ]; then
    exit 0
fi

TASKOPS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if command -v cygpath &>/dev/null; then
    TASKOPS_ROOT="$(cygpath -w "$TASKOPS_ROOT")"
fi
export PYTHONPATH="$TASKOPS_ROOT${PYTHONPATH:+;$PYTHONPATH}"
DB_PATH=$(find . -maxdepth 2 -name "taskops.db" 2>/dev/null | head -1)

if [ -z "$DB_PATH" ]; then
    exit 0
fi

ACTIVE_TASK=$(python -m cli --db "$DB_PATH" workflow current 2>/dev/null)

TOOL_NAME="${CLAUDE_TOOL_NAME:-unknown}"

if [ -n "$ACTIVE_TASK" ]; then
    python -m cli --db "$DB_PATH" op progress "$ACTIVE_TASK" \
        --summary "Tool used: $TOOL_NAME" 2>/dev/null
fi

python -m cli --db "$DB_PATH" monitor record \
    --event tool_use \
    --tool "$TOOL_NAME" \
    --task "${ACTIVE_TASK:-}" \
    --source hook 2>/dev/null
