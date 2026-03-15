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

```bash
# Record task start
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
```

## Status Queries / 상태 조회

```bash
# Project-wide status summary with progress percentage
python -m cli query status

# Filter tasks by status
python -m cli query tasks --status in_progress

# Regenerate TODO.md from current state
python -m cli query generate-todo

# Generate operations report (TASK_OPERATIONS.md)
python -m cli query generate-ops
```

## Best Practices / 모범 사례

1. Always `op start` before beginning work on a task
2. Record `op progress` at meaningful milestones, not every small change
3. Include specific details in summaries (file names, counts, what was done)
4. Use `op error` for blockers that need resolution
5. Use `op interrupt` when switching away from a task temporarily
6. Run `query generate-todo` after completing tasks to keep TODO.md current
