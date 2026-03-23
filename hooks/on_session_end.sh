#!/bin/bash
# Hook: Called when a Claude Code session ends (StopHook)
# TaskOps Hook: 세션 종료 시 JSONL 파싱 → agent_events 자동 임포트
#
# Registration in .claude/settings.json:
#   "hooks": {
#     "Stop": [
#       {
#         "matcher": "",
#         "hooks": [
#           { "type": "command", "command": "/path/to/taskops/hooks/on_session_end.sh" }
#         ]
#       }
#     ]
#   }
#
# Safety: Only fires when TaskOps is the active tracking system.

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

python -m cli --db "$DB_PATH" monitor parse --auto 2>/dev/null

exit 0
