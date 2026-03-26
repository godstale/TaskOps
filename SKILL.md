---
name: taskops
description: >
  Use when a project plan or implementation spec has been finalized and execution is about to begin,
  or a session starts on a project that already has a taskops.db.

  When starting work:
  - Register a workflow and import the full work plan (all tasks/epics) with workflow_id.
  - Before execution begins, register verifiable end-goals as Objectives (milestone = success criteria).
  - When resuming an existing workflow, always check registered Objectives first.

  During execution:
  - Signal task start (`op start`) and completion (`op complete`) for every task.
  - Record progress and errors via `op progress` / `op error`.
  - Register resources as they are created — not only at session end.

  When work is complete:
  - Review each Objective: update status to 'done' or 'cancelled'.
  - Register a retrospective Objective summarizing results, gaps, and lessons learned.
  - Submit a workflow completion report via `workflow report`.

  When re-executing:
  - Run `workflow restart <W-ID>` first — resets tasks AND clears all operations.
  - Register new Objectives capturing cautions and lessons before starting.
---

# TaskOps — Project Management Skill for Claude Code

## ⚠️ Common Mistakes (Gotchas)

| Mistake | Fix |
|---------|-----|
| Missing `--workflow <W-ID>` on `epic create`, `task create`, `objective create` | Always pass `--workflow`; use `workflow import` for bulk creation |
| Using `epic create`/`task create` individually | `workflow import` is the **only valid plan registration path** |
| Not setting `TASKOPS_DB` env var | `export TASKOPS_DB=/absolute/path/to/project/taskops.db` first |
| Creating a new workflow without checking for duplicates | Always run `workflow list` before `workflow create` |
| Marking task done without resource registration | `resource add <T-ID>` then verify `resource list --task <T-ID>` non-empty |
| Not registering Objectives before execution starts | `objective create` before first `op start` |
| Not doing post-work Objective review | After final task: `objective list` → update statuses → register retrospective |
| Not clearing operations when restarting | `workflow restart <W-ID>` resets tasks + clears ops — no extra flag needed |
| Leaving a task `in_progress` when work stops | Close with `op complete` or `task update --status interrupted` |

---

## Phase 1: Initialization

```bash
# 1. Set env vars
export TASKOPS_DB=/absolute/path/to/project/taskops.db
export TASKOPS_ACTIVE=1

# 2. Initialize project
python -m cli init --name "Project Name" --prefix PRJ

# 3. Check for existing workflows (duplicate detection — always run first)
python -m cli workflow list

# 4. Create workflow (always include --description)
python -m cli workflow create \
  --title "My Plan" \
  --description "Brief description of scope and intent"
# → Workflow ID: PRJ-MP
```

### Configure Hooks (optional)

Register in `.claude/settings.json` (project-level):

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write|Bash|Agent",
      "command": "bash /path/to/TaskOps/hooks/on_tool_use.sh"
    }]
  }
}
```

Hook guard: `on_tool_use.sh` only fires when `TASKOPS_ACTIVE=1`.
Agent tool calls are automatically recorded as `op progress --subagent true`.

---

## Phase 2: Planning

```bash
# Import full ETS plan in one call — never use individual epic/task create
python -m cli workflow import PRJ-MP --structure '<json>'

# Register goals as Objectives BEFORE execution
python -m cli objective create --workflow PRJ-MP \
  --title "All endpoints migrated and tested" \
  --milestone "REST → async migration complete"

# Verify
python -m cli query show --workflow PRJ-MP
```

JSON structure for `workflow import`:
```json
{
  "epics": [{
    "title": "Epic title",
    "tasks": [{
      "title": "Task title",
      "tasks": [{"title": "SubTask title"}]
    }]
  }]
}
```

→ Full planning guide: `skills/fragments/planning-guide.md`

---

## Phase 3: Execution

```bash
# Find next task
python -m cli workflow next --workflow PRJ-MP

# Per-task sequence:
python -m cli task update <T-ID> --status in_progress
python -m cli op start <T-ID> --platform claude_code

# ... do work, record key milestones:
python -m cli op progress <T-ID> --summary "Implemented login endpoint"

# ⛔ RESOURCE GATE — register ALL outputs before marking done:
python -m cli resource add <T-ID> --path ./file --type output --desc "description"
python -m cli resource list --task <T-ID>   # must be non-empty

python -m cli task update <T-ID> --status done
python -m cli op complete <T-ID> --summary "Task complete"
```

**Manual recording required for:**
- Skill invoked: `--summary "Skill: brainstorming — scope defined"`
- MCP/plugin called: `--summary "MCP: playwright — login flow tested"`
- Key decision: `--summary "Decision: JWT over session cookies"`
- Memory files: `resource add <T-ID> --path ./.claude/memory/feedback.md --type output`

→ Full execution guide: `skills/fragments/execution-guide.md`
→ Operations recording: `skills/fragments/monitoring-guide.md`

---

## Phase 4: Completion

```bash
# Check status
python -m cli query status --workflow PRJ-MP

# Review and update each Objective
python -m cli objective list --workflow PRJ-MP
python -m cli objective update PRJ-MP-O001 --status done
python -m cli objective update PRJ-MP-O002 --status cancelled

# Register retrospective
python -m cli objective create --workflow PRJ-MP \
  --title "Retrospective: ..." \
  --milestone "What went well, what was lacking, what to avoid next time"

# Submit completion report
python -m cli workflow report PRJ-MP \
  --summary "One-sentence summary" \
  --details "Full markdown: what was built, key decisions, files created"
```

---

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
python -m cli workflow restart <W-ID>   # reset tasks to todo + clear all ops
python -m cli project restart           # reset ALL tasks project-wide
```

---

## CLI Reference

→ Full grouped commands: `skills/fragments/cli-reference.md`

Key command groups:
- **Workflow**: `create`, `list`, `import`, `export`, `report`, `restart`, `delete`
- **ETS**: `epic`, `task`, `objective` (all require `--workflow`)
- **Operations**: `op start/progress/complete/error/interrupt/log`
- **Resources**: `resource add/list`
- **Query**: `query status/show/tasks`
- **Settings**: `setting set/get/list/delete` (require `--workflow`)

---

## TaskBoard (Visual Monitor)

```bash
# TUI (terminal)
pnpm --filter @taskboard/tui dev -- --path /path/to/project-root
```

TaskBoard watches `taskops.db` and refreshes automatically.
→ [TaskBoard GitHub](https://github.com/godstale/TaskBoard)
