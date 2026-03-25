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

## Events Requiring Manual Recording / 수동 기록이 필요한 이벤트

Hooks auto-record subagent dispatch. Skill invocations, MCP/plugin calls, and key decisions must be recorded manually:

| Event | Command |
|-------|---------|
| Skill invoked | `python -m cli op progress {T-ID} --summary "Skill: [name] — [purpose]"` |
| MCP / plugin called | `python -m cli op progress {T-ID} --summary "MCP: [name] — [action]"` |
| Key decision made | `python -m cli op progress {T-ID} --summary "Decision: [what was decided]"` |

Memory and system files must be registered as resources **at the time they are created or modified**:

```bash
# Memory file written
python -m cli resource add {T-ID} \
  --path ./.claude/memory/feedback_xyz.md --type output --desc "memory: feedback on X"

# System / config file modified
python -m cli resource add {T-ID} \
  --path ./.claude/settings.json --type output --desc "system: PostToolUse hooks added"
```

---

## Best Practices / 모범 사례

1. Always `op start` before beginning work on a task
2. Record `op progress` at meaningful milestones, not every small change
3. Include specific details in summaries (file names, counts, what was done)
4. Use `op error` for blockers that need resolution
5. Use `op interrupt` when switching away from a task temporarily
6. **Before marking a task done:** register ALL artifacts (including intermediate files) with `resource add`, then verify with `resource list --task <T-ID>`. Do NOT run `task update --status done` until the list is non-empty and complete.
