#!/bin/bash
# Hook: Called when agent completes a task
# TaskOps Hook: Task 완료 시 호출
# Usage: bash on_task_complete.sh <TASK_ID>

TASK_ID="$1"
if [ -z "$TASK_ID" ]; then
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

python -m cli --db "$DB_PATH" task update "$TASK_ID" --status done 2>/dev/null
python -m cli --db "$DB_PATH" op complete "$TASK_ID" --summary "Task completed" 2>/dev/null
python -m cli --db "$DB_PATH" query generate-todo 2>/dev/null
