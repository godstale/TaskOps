# Workflow Guide / Workflow 가이드

## Workflow Model / Workflow 모델

Workflow is defined by three fields on each Task:

| Field | Purpose | Example |
|-------|---------|---------|
| `seq_order` | Execution order (integer) | `1`, `2`, `3` |
| `parallel_group` | Concurrent execution group (NULL = sequential) | `"auth-group"` |
| `depends_on` | Prerequisite Task IDs (JSON array) | `["TST-T001"]` |

## Execution Logic / 실행 로직

1. Sort by `seq_order`
2. Same `seq_order` + same `parallel_group` = can run concurrently
3. All tasks in `depends_on` must be `done` before execution
4. `status=todo` + above conditions met = next executable task

## Defining Workflow / Workflow 정의

```bash
# Set sequential order (assigns seq_order 1, 2, 3, ...)
python -m cli workflow set-order {PREFIX}-T001 {PREFIX}-T002 {PREFIX}-T003

# Group tasks for parallel execution
python -m cli workflow set-parallel --group "auth-group" {PREFIX}-T002 {PREFIX}-T003

# Add dependency (T004 depends on T002 and T003)
python -m cli workflow add-dep {PREFIX}-T004 --depends-on {PREFIX}-T002 {PREFIX}-T003
```

## Querying Workflow / Workflow 조회

```bash
# Show full workflow with groups and dependencies
python -m cli workflow show

# Get next executable task(s)
python -m cli workflow next

# Get currently in-progress task
python -m cli workflow current
```

## Example / 예시

```
seq_order=1  TST-T001 (group=NULL)           → Runs first, alone
seq_order=2  TST-T002 (group="auth-group")   → After T001 done
seq_order=2  TST-T003 (group="auth-group")   → Runs concurrently with T002
seq_order=3  TST-T004 (depends_on=["TST-T002","TST-T003"])
                                              → After T002 AND T003 done
```
