# Monitoring Guide / 모니터링 가이드

## Operations Recording / 작업 기록

Record operations to track agent progress on each task.

### Operation Types / 작업 유형

| Type | When to Record | Example |
|------|---------------|---------|
| `start` | Beginning work on a task | Starting implementation |
| `progress` | Completing a meaningful step | "Implemented 3 of 5 endpoints" |
| `complete` | Task is finished | "All tests passing" |
| `error` | Encountered a blocking error | "API authentication failed" |
| `interrupt` | Pausing work on a task | "Waiting for API key from team" |

### CLI Commands / CLI 명령어

> `op` commands automatically resolve `workflow_id` from the task's own `workflow_id` field.
> No need to pass `--workflow` explicitly unless you need to override it.

```bash
# Record task start (workflow_id auto-resolved from task)
python -m cli op start {TASK_ID} --platform claude_code

# Record progress (include meaningful summary)
python -m cli op progress {TASK_ID} --summary "Implemented login endpoint"

# Record progress with subagent info
python -m cli op progress {TASK_ID} --summary "Tests written" --subagent true

# Record completion
python -m cli op complete {TASK_ID} --summary "Feature complete, all tests pass"

# Record error
python -m cli op error {TASK_ID} --summary "Database connection failed"

# Record interruption
python -m cli op interrupt {TASK_ID} --summary "Blocked on external dependency"

# View operation log
python -m cli op log --task {TASK_ID}
python -m cli op log --workflow {WORKFLOW_ID}
```

## Status Queries / 상태 조회

```bash
# Project-wide status summary with progress percentage
python -m cli query status

# Workflow-scoped status
python -m cli query status --workflow {WORKFLOW_ID}

# Filter tasks by status
python -m cli query tasks --status in_progress

# Filter tasks by workflow
python -m cli query tasks --workflow {WORKFLOW_ID}

# Query operation history directly from DB
python -m cli op log
python -m cli op log --task <TASK_ID>
python -m cli op log --workflow <WORKFLOW_ID>
```

## Agent Activity Monitoring / 에이전트 활동 모니터링

Automatically tracks tool usage, thinking, and subagent events per session.
훅을 통해 도구 사용, 사고, 서브에이전트 이벤트를 세션 단위로 자동 추적합니다.

### How it works / 동작 방식

- `on_tool_use.sh` hook records each tool call automatically → no manual action needed
- `on_session_end.sh` hook parses the JSONL session file at session end (register as `Stop` hook)
- `monitor record` is called by hooks; **do not call it directly**

### CLI Commands / CLI 명령어

```bash
# Parse the latest JSONL session file and import events into DB
python -m cli monitor parse --auto

# Parse a specific session
python -m cli monitor parse --session <session-hash>

# Associate parsed events with a workflow
python -m cli monitor parse --auto --workflow {WORKFLOW_ID}

# Tool usage report (all workflows)
python -m cli monitor report

# Tool usage report scoped to a workflow
python -m cli monitor report --workflow {WORKFLOW_ID}

# Session summary (most recent session)
python -m cli monitor summary

# Session summary for a specific session
python -m cli monitor summary --session <session-hash>
```

### Report output columns / 리포트 출력 컬럼

| Column | Description |
|--------|-------------|
| Tool   | Tool name |
| Calls  | Total call count |
| Avg ms | Average duration (JSONL source only) |
| %      | Percentage of total calls |

---

## Best Practices / 모범 사례

1. Always `op start` before beginning work on a task
2. Record `op progress` at meaningful milestones, not every small change
3. Include specific details in summaries (file names, counts, what was done)
4. Use `op error` for blockers that need resolution
5. Use `op interrupt` when switching away from a task temporarily
6. **Before marking a task done:** register ALL artifacts (including intermediate files) with `resource add`, then verify with `resource list --task <T-ID>`. Do NOT run `task update --status done` until the list is non-empty and complete.
