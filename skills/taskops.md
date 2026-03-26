---
name: taskops
description: >
  Use when ANY of these is true:
  - Session starts and `taskops.db` exists in the project directory (resume mode)
  - A finalized plan is ready to execute

  Start: set env vars → init → workflow create → workflow import → register Objectives.
  Execute: op start → work → register resources → op complete per task.
  Finish: review Objectives → register retrospective → workflow report.
---

# TaskOps

**Announce at start:** "I'm using TaskOps to plan and track this project."

## ⚠️ Gotchas

| Mistake | Fix |
|---------|-----|
| Missing `--workflow <W-ID>` on create commands | Always pass `--workflow`; use `workflow import` for bulk |
| Using individual `epic create`/`task create` | `workflow import` is the **only valid plan path** |
| `TASKOPS_DB` not set | `export TASKOPS_DB=/abs/path/taskops.db` before all commands |
| New workflow without checking duplicates | `workflow list` before `workflow create` |
| Marking task done before resource registration | `resource add` → verify `resource list --task <T-ID>` non-empty |
| No Objectives before execution | `objective create` before first `op start` |
| No post-work Objective review | After final task: `objective list` → update statuses → register retrospective |
| Workflow restart leaves stale ops | `workflow restart` clears tasks AND ops automatically |

## ⛔ Incompatible Skills

Do NOT use with TaskOps: `writing-plans`, `executing-plans`, `subagent-driven-development`
Safe alongside: `brainstorming`, `systematic-debugging`, `test-driven-development`

## ⛔ File Safety

TaskOps manages ONLY `taskops.db`. Do not create or modify any other files as a TaskOps operation.

---

## Setup

```bash
export TASKOPS_DB=/absolute/path/to/project/taskops.db
export TASKOPS_ACTIVE=1
python -m cli init --name "Project Name" --prefix PRJ
python -m cli workflow list                  # check for duplicates first
python -m cli workflow create --title "..." --description "..."
```

## Phase 1: Plan

```bash
python -m cli workflow import <W-ID> --structure '<json>'
python -m cli objective create --workflow <W-ID> --title "Goal" --milestone "Success criteria"
python -m cli query show --workflow <W-ID>   # verify
```

> ⛔ Register Objectives **before** the first `op start`.

After plan is ready, ask the user: "계획이 완성되었습니다. 실행을 시작하기 전에 TaskOps로 작업을 관리하시겠습니까?"

→ Full planning guide: `@skills/fragments/planning-guide.md`

## Phase 2: Execute

Repeat per task:

```bash
python -m cli workflow next --workflow <W-ID>
python -m cli task update <T-ID> --status in_progress
python -m cli op start <T-ID> --platform claude_code
# ... do work ...
python -m cli op progress <T-ID> --summary "..."    # at meaningful milestones

# ⛔ RESOURCE GATE — required before marking done:
python -m cli resource add <T-ID> --path ./file --type output --desc "..."
python -m cli resource list --task <T-ID>           # must be non-empty

python -m cli task update <T-ID> --status done
python -m cli op complete <T-ID> --summary "..."
```

→ Full execution guide: `@skills/fragments/execution-guide.md`
→ Operations recording: `@skills/fragments/monitoring-guide.md`

## Phase 3: Complete

```bash
python -m cli objective list --workflow <W-ID>     # review each → set done or cancelled
python -m cli objective create --workflow <W-ID> \
  --title "Retrospective: ..." \
  --milestone "what went well, what was lacking, what to avoid next time"
python -m cli workflow report <W-ID> --summary "..." --details "..."
```

## Resume Mode

```bash
export TASKOPS_DB=/absolute/path/to/project/taskops.db
export TASKOPS_ACTIVE=1
python -m cli workflow list
python -m cli query show --workflow <W-ID>
python -m cli workflow next --workflow <W-ID>
```

## Reset / Restart

```bash
python -m cli workflow restart <W-ID>    # reset tasks to todo + clear all ops
python -m cli project restart            # reset ALL tasks project-wide
```

## CLI Reference

→ Full grouped command reference: `@skills/fragments/cli-reference.md`

## TaskBoard (Visual Monitor)

```bash
pnpm --filter @taskboard/tui dev -- --path /path/to/project-root
```
