---
name: taskops
description: >
  Use when user explicitly requests TaskOps, wants to manage a TODO list as tracked tasks,
  has a plan/spec and wants to start execution, wants to monitor AI execution progress,
  or a session starts on a project that already has taskops.db.
conflicts:
  mutual_exclusive:
    - writing-plans
    - executing-plans
    - subagent-driven-development
  safe_before:
    - brainstorming
---

# TaskOps — Project Management Skill for Claude Code

**Announce at start:** "I'm using TaskOps to plan and track this project."

## When to Invoke

Trigger conditions (any one is sufficient):
- User explicitly requests TaskOps
- User wants to manage a TODO list as tracked tasks
- User wants to monitor AI execution progress
- Session starts and `taskops.db` exists in the project directory (resume mode)
- User creates a plan and wants to track execution across sessions

## ⚠️ TaskOps Replaces These Superpowers Skills

When TaskOps is active, these skills are **incompatible** — they use conflicting tracking systems (TodoWrite vs. SQLite):

| Skill | TaskOps replacement |
|-------|-------------------|
| `writing-plans` | `workflow import` + `@skills/fragments/planning-guide.md` |
| `executing-plans` | `op start/complete` + `@skills/fragments/execution-guide.md` |
| `subagent-driven-development` | TaskOps workflow-level task management |

**Safe to use alongside TaskOps:**
- `brainstorming` — Run BEFORE activation; its output feeds into `workflow import`
- `systematic-debugging`, `test-driven-development` — Code-level tools; no conflict
- `verification-before-completion`, `requesting-code-review` — No tracking conflict

## Prerequisites

- Python 3.10+
- TaskOps repository cloned (contains `cli/` package and `hooks/`)

---

## ⛔ File Safety Rule

**TaskOps manages ONLY `taskops.db`.** Do NOT create, modify, or delete any other files as part of a TaskOps operation. This means: no source files, no README, no CLAUDE.md, no TODO.md, no SETTINGS.md.

Exception: `workflow export` may create a TODO.md file **only when the user explicitly requests it**.

---

## Handling Reset Requests

When user asks to "reset" or "start over", always ask which type:

> **Option 1 — 상태만 초기화 (Keep plan, reset status)**
> `python -m cli workflow restart {PREFIX}-W001`
>
> **Option 2 — 계획부터 다시 시작 (Delete plan, re-plan)**
> `python -m cli workflow delete {PREFIX}-W001` → re-run planning phase

⚠️ Neither option touches project source files.

---

## Phase 1: Initialization

> **Path Rule:** Run `python -m cli` from the TaskOps repo directory. Set `TASKOPS_DB` to the absolute path of the project's DB file.

**Required setup sequence:**

```bash
# 1. Set DB path and activate hooks
export TASKOPS_DB=/absolute/path/to/project/taskops.db
export TASKOPS_ACTIVE=1

# 2. Initialize project (creates taskops.db only)
python -m cli init --name "Project Name" --prefix PRJ

# 3. Create workflow (all tasks must belong to a workflow)
python -m cli workflow create --title "My Plan"
# → Workflow ID: PRJ-W001
```

> Step 3 is required. Tasks without a `workflow_id` are invisible in TaskBoard and cannot be workflow-filtered.

Hook configuration (optional):
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write|Bash",
      "command": "bash /path/to/TaskOps/hooks/on_tool_use.sh"
    }]
  }
}
```

> Hook guard: `on_tool_use.sh` only fires when `TASKOPS_ACTIVE=1`.

---

## Phase 2: Planning

Follow `@skills/fragments/planning-guide.md` for full planning instructions.

Key principle: `workflow import` is the only valid plan registration path. Never use individual `epic create` / `task create` calls.

For ETS structure rules, see `@skills/fragments/ets-planning.md`.
For setting/dependency configuration, see `@skills/fragments/setting-guide.md`.

---

## ⛔ Planning Gate

After plan import, ALWAYS ask before starting execution:

> "계획이 완성되었습니다. 실행을 시작하기 전에 TaskOps로 작업을 관리하시겠습니까?"

- **User agrees** → Phase 3 Execution
- **User declines** → use `writing-plans` + `executing-plans`. Do not invoke TaskOps further.

---

## Phase 3: Execution

Follow `@skills/fragments/execution-guide.md` for full execution instructions.

**Required op recording sequence for every task:**
1. `op start {T-ID}` → work → `op progress {T-ID}` (at milestones)
2. `resource add {T-ID}` for every artifact (HARD GATE before done)
3. `resource list --task {T-ID}` to verify (must be non-empty)
4. `task update {T-ID} --status done` → `op complete {T-ID}`

For operations recording detail, see `@skills/fragments/monitoring-guide.md`.

---

## Phase 4: Monitoring

```bash
python -m cli query status --workflow {PREFIX}-W001
python -m cli query show --workflow {PREFIX}-W001
python -m cli op log --workflow {PREFIX}-W001
python -m cli workflow next --workflow {PREFIX}-W001
```

---

## Phase 5: Rollback & Restart

```bash
# Create checkpoint at any point
python -m cli project checkpoint --note "After T003 complete"

# List checkpoints
python -m cli project checkpoint list

# Roll back to checkpoint (auto-saves current state first)
python -m cli project rollback --checkpoint 2

# Reset specific workflow tasks to todo
python -m cli workflow restart {PREFIX}-W001

# Reset ALL tasks to todo (project-wide)
python -m cli project restart
```

---

## Resume Mode (Existing DB)

When `taskops.db` exists at session start:

```bash
export TASKOPS_DB=/absolute/path/to/project/taskops.db
export TASKOPS_ACTIVE=1

# Check what workflows exist
python -m cli workflow list

# Load task structure for a specific workflow
python -m cli query show --workflow {PREFIX}-W001

# Find the next task
python -m cli workflow next --workflow {PREFIX}-W001
```

---

## Reference: All CLI Commands

| Command | Description |
|---------|-------------|
| `init --name --prefix [--path]` | Initialize project (creates taskops.db only) |
| `workflow create --title` | Create a workflow (plan container) |
| `workflow list` | List all workflows |
| `workflow import <W-ID> --structure '<json>'` | Import full ETS plan (required path) |
| `workflow import <W-ID> --structure-file <path>` | Import from JSON file |
| `workflow export <W-ID> [--output <path>]` | Export to TODO.md (default: next to DB) |
| `workflow delete <W-ID>` | Delete workflow and all its tasks |
| `workflow restart <W-ID> [--clear-ops]` | Reset workflow tasks to todo |
| `workflow show [--workflow <W-ID>]` | Show execution order |
| `workflow next [--workflow <W-ID>]` | Show next executable tasks |
| `workflow current [--workflow <W-ID>]` | Show active task |
| `workflow set-order <T-ID>...` | Set sequential execution order |
| `workflow set-parallel --group <name> <T-ID>...` | Group for parallel execution |
| `workflow add-dep <T-ID> --depends-on <T-ID>...` | Add task dependency |
| `epic create --title [--workflow <W-ID>]` | Create epic |
| `epic list/show/update/delete` | Epic management |
| `task create --parent --title [--workflow <W-ID>]` | Create task |
| `task list [--epic] [--status] [--workflow <W-ID>]` | List tasks |
| `task show/update/delete` | Task management |
| `task update <T-ID> --status <status>` | Status: todo\|in_progress\|interrupted\|done\|cancelled |
| `objective create --title [--workflow <W-ID>]` | Create milestone marker |
| `objective list/update/delete` | Objective management |
| `plan update --changes '<json>' [--workflow <W-ID>]` | Partial plan changes |
| `op start/progress/complete/error/interrupt <T-ID>` | Record operation (workflow_id auto-resolved) |
| `op log [--task <T-ID>] [--workflow <W-ID>]` | View operation history |
| `resource add <T-ID> --path --type --desc` | Register artifact (workflow_id auto-resolved) |
| `resource list [--task <T-ID>] [--workflow <W-ID>] [--type]` | List artifacts |
| `query show [--workflow <W-ID>]` | Full task tree view |
| `query status [--workflow <W-ID>]` | Progress summary |
| `query tasks [--status] [--workflow <W-ID>]` | Filtered task list |
| `setting set/get/list/delete` | Dependency/configuration management |
| `project checkpoint [--note]` | Create status snapshot |
| `project checkpoint list` | List snapshots |
| `project rollback --checkpoint <id>` | Restore task statuses from snapshot |
| `project restart [--clear-ops]` | Reset all tasks to todo |

**workflow_id rules:**

| How task is created | workflow_id |
|---------------------|-------------|
| `workflow import` | ✅ Set automatically |
| `epic/task/objective create`, `plan update` | ⚠️ Pass `--workflow <W-ID>` explicitly |
| `op start/progress/complete/error/interrupt` | ✅ Auto-resolved from task |
| `resource add` | ✅ Auto-resolved from task |

---

## Visualizing with TaskBoard

TaskBoard is a read-only GUI that visualizes `taskops.db` in real-time.

**Launch (from TaskBoard directory):**
```bash
pnpm --filter @taskboard/tui dev -- --path /path/to/project-root
```

**Detect installation:**
1. `$TASKBOARD_PATH` env var
2. `~/TaskBoard`
3. `./TaskBoard` (relative to cwd)

→ [TaskBoard GitHub](https://github.com/godstale/TaskBoard)
