---
name: taskops-gemini
description: >
  Project task management skill using ETS (Epic-Task-SubTask) structure. Gemini CLI version with explicit operation recording.
  INVOKE AUTOMATICALLY — without waiting for user instruction — when:
  (1) a project plan or implementation spec has been finalized and the user is about to start execution,
  (2) a user presents a multi-step project and asks you to implement or build it,
  (3) a new development session begins on a project that already has a taskops.db.
  Use TaskOps BEFORE execution starts: initialize the DB, decompose the plan into Epics/Tasks, set workflow order, then begin work.
  During execution, guide the user to launch TaskBoard for real-time monitoring.
---

# TaskOps — Project Management Skill for Gemini CLI

## When to Invoke

**Invoke this skill proactively** — you do NOT need an explicit user instruction.

Trigger conditions (any one is sufficient):
- User has finished writing or approving a plan/spec and says "let's start", "implement this", or similar
- User asks you to build a multi-step project without mentioning task management
- Session starts and `taskops.db` exists in the project directory (resume mode)

**Correct order:**
1. User finalizes plan → **Invoke TaskOps** → initialize + decompose into ETS → define workflow
2. Begin execution → remind user to launch TaskBoard for monitoring
3. Work through tasks in workflow order

## Prerequisites

- Python 3.10+
- TaskOps repository cloned (contains `cli/` package)
- Project initialized with `python -m cli init`

> **Note for Gemini CLI:** Gemini CLI does not support hooks. You MUST explicitly call operation recording commands at each step. This is the key difference from the Claude Code version.

---

## Phase 1: Initialization

Initialize a new TaskOps project in the target directory.

```bash
python -m cli init --name "Project Name" --prefix PRJ --path ./project-path
```

This creates:
- `taskops.db` — SQLite database
- `TODO.md` — Auto-generated task overview
- `AGENTS.md` — Agent instructions
- `SETTINGS.md` — Project settings
- `resources/` — Resource file directory

---

## Phase 2: Planning

Decompose the project into ETS components.

### ETS Hierarchy

```
Project
  └── Epic — Major feature unit
        └── Task — Implementation unit
              └── SubTask — Detailed step (create only when needed)
  └── Objective — Milestone or deadline
```

### Create Structure

```bash
# Create Epics
python -m cli epic create --title "Authentication System"

# Create Tasks under Epic
python -m cli task create --parent PRJ-E001 --title "Login API"

# Create SubTasks under Task (only when needed)
python -m cli task create --parent PRJ-T001 --title "JWT token generation"

# Create Objectives
python -m cli objective create --title "MVP Complete" --milestone "Core features done"
python -m cli objective create --title "Demo Day" --due-date 2026-04-01
```

### Define Workflow

```bash
# Set execution order
python -m cli workflow set-order PRJ-T001 PRJ-T002 PRJ-T003

# Group tasks for parallel execution
python -m cli workflow set-parallel --group "auth-group" PRJ-T002 PRJ-T003

# Add dependencies
python -m cli workflow add-dep PRJ-T004 --depends-on PRJ-T002 PRJ-T003
```

### Updating the Plan

When the user modifies the project plan (adds, removes, or renames tasks or epics), apply changes to the DB before continuing:

```bash
python -m cli plan update --changes '<json>'
```

JSON format:
```json
{
  "create": [
    {"type": "epic", "title": "New Epic"},
    {"type": "task", "title": "New Task", "parent_id": "PRJ-E001"}
  ],
  "update": [{"id": "PRJ-T001", "title": "...", "status": "..."}],
  "delete": [{"id": "PRJ-T002"}]
}
```

Note: `parent_id` is **required** for `type: "task"` and must reference an existing epic or task. Any of `create`, `update`, `delete` may be omitted. After a successful update, `TODO.md` is regenerated automatically.

### Generate TODO.md

```bash
python -m cli query generate-todo
```

---

## Phase 3: Execution

### Launch TaskBoard (Optional — Real-time Monitoring)

Before starting work, check if TaskBoard is available and offer to launch it.

**Step 1 — Detect installation** (check in order):
1. `$TASKBOARD_PATH` environment variable
2. `~/TaskBoard`
3. `./TaskBoard` (relative to cwd)

**Step 2 — If found**, launch TUI in a separate terminal (from the TaskBoard directory):
```bash
pnpm --filter @taskboard/tui dev -- --path /path/to/project-root
```

**Step 3 — If not found**, notify the user and continue without it:
> TaskBoard is not installed. Work will proceed normally.
> See [Visualizing with TaskBoard](#visualizing-with-taskboard) for install steps.

> TaskBoard watches `taskops.db` and refreshes automatically as tasks progress.

Work through tasks following the workflow order.

> **IMPORTANT:** Since Gemini CLI has no hooks, you MUST manually call the operation recording commands at each step.

### Start a Task

```bash
# Check next executable task
python -m cli workflow next

# REQUIRED: Update status and record start
python -m cli task update PRJ-T001 --status in_progress
python -m cli op start PRJ-T001 --platform gemini_cli
```

### Record Progress

After completing meaningful milestones during implementation:

```bash
# REQUIRED: Record progress with descriptive summary
python -m cli op progress PRJ-T001 --summary "Implemented 3 of 5 endpoints"
```

Record progress at these points:
- After implementing a major component
- After writing or passing tests
- After resolving a significant issue
- Before switching to a different task

### Complete a Task

```bash
# REQUIRED: Mark done, record completion, regenerate TODO
python -m cli task update PRJ-T001 --status done
python -m cli op complete PRJ-T001 --summary "Login API complete, all tests pass"
python -m cli query generate-todo
```

### Handle Interruptions

```bash
python -m cli task update PRJ-T001 --status interrupted --interrupt "Waiting for API key"
python -m cli op interrupt PRJ-T001 --summary "Blocked on external dependency"
```

### Handle Errors

```bash
python -m cli op error PRJ-T001 --summary "Database connection failed"
```

---

## Phase 4: Monitoring

### Check Project Status

```bash
# Overall status with progress percentage
python -m cli query status

# List tasks by status
python -m cli query tasks --status in_progress

# View operation log for a task
python -m cli op log --task PRJ-T001

# View full workflow
python -m cli workflow show
```

### Regenerate Reports

```bash
python -m cli query generate-todo
```

### Manage Resources

```bash
python -m cli resource add PRJ-T001 --path ./docs/spec.md --type input --desc "API spec"
python -m cli resource list --task PRJ-T001
```

### Manage Settings

```bash
python -m cli setting set commit_style "conventional" --desc "Commit message style"
python -m cli setting get commit_style
python -m cli setting list
```

---

---

## Phase 5: Rollback & Restart

Use when a task needs to be retried, the project needs to return to a known-good state, or execution must restart from scratch.

### Task Status Rollback

Roll back a single task to a previous status using the existing `task update` command:

```bash
# Set a completed task back to todo (re-run it)
python -m cli task update PRJ-T003 --status todo

# Set a task to interrupted with a reason
python -m cli task update PRJ-T003 --status interrupted --interrupt "Needs redesign"

# Regenerate TODO.md after any status change
python -m cli query generate-todo
```

### Checkpoint Rollback

Capture the current state as a snapshot and roll back to any previous snapshot:

```bash
# Create a checkpoint at any meaningful point during execution
python -m cli project checkpoint --note "After T003 complete"

# List all checkpoints
python -m cli project checkpoint list

# Roll back all task statuses to a checkpoint
# (auto-saves current state as a safety checkpoint first)
python -m cli project rollback --checkpoint 2

# Regenerate TODO.md after rollback
python -m cli query generate-todo
```

> Checkpoint snapshots preserve `status` and `interrupt` fields for all tasks.
> Operation history is NOT rolled back — the log is always preserved.
> Tasks created after the checkpoint are reset to `todo` on rollback.

### Project Restart

Reset all tasks to `todo` and start over:

```bash
# Reset all tasks to todo (operation history preserved)
python -m cli project restart

# Reset all tasks to todo AND clear operation history
python -m cli project restart --clear-ops

# Regenerate TODO.md after restart
python -m cli query generate-todo
```

> `project restart` automatically creates a checkpoint before resetting, so you can roll back if needed.

---

## Gemini CLI Tool Mapping

| Claude Code Tool | Gemini CLI Equivalent |
|-----------------|----------------------|
| `Edit` | `edit_file` |
| `Write` | `write_file` |
| `Read` | `read_file` |
| `Bash` | `run_shell` |
| `Glob` | `list_files` |
| `Grep` | `search_files` |

---

## Reference: All CLI Commands

| Command | Description |
|---------|-------------|
| `init --name --prefix --path` | Initialize project |
| `epic create/list/show/update/delete` | Epic CRUD |
| `task create/list/show/update/delete` | Task/SubTask CRUD |
| `objective create/list/update/delete` | Objective CRUD |
| `plan update --changes <json>` | Update plan: create/update/delete tasks and epics |
| `workflow set-order/set-parallel/add-dep/show/next/current` | Workflow management |
| `op start/progress/complete/error/interrupt/log` | Operations recording |
| `resource add/list` | Resource management |
| `query status/tasks/generate-todo` | Status queries and reports |
| `setting set/get/list/delete` | Settings management |
| `project checkpoint [--note]` | Create a status snapshot |
| `project checkpoint list` | List all checkpoints |
| `project rollback --checkpoint <id>` | Restore task statuses from checkpoint |
| `project restart [--clear-ops]` | Reset all tasks to todo |

All commands use: `python -m cli [--db path] <command> <subcommand> [options]`

---

## Visualizing with TaskBoard

TaskBoard is a standalone read-only GUI that visualizes the TaskOps database in real-time.
Two interface modes are available: TUI (terminal, stable) and Electron (desktop, experimental).

### Install

```bash
git clone https://github.com/godstale/TaskBoard.git
cd TaskBoard
pnpm install
```

> **Windows PowerShell users:** run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
> or use Git Bash / Command Prompt instead.

### TUI Mode (Stable)

**Quick start — dev mode (no build required):**
```bash
# Run from the TaskBoard directory
pnpm --filter @taskboard/tui dev -- --path /path/to/project-root
```

**Production — build first, then run:**
```bash
pnpm --filter @taskboard/tui build
node packages/tui/dist/index.js --path /path/to/project-root
```

**Key controls:** `Tab` switch screen · `R` reload · `Q` quit · `↑↓` navigate · `Enter` select

### Electron Mode (Experimental)

**Dev mode:**
```bash
# First-time setup — rebuild native modules for your Node version
pnpm rebuild:electron

# Launch
pnpm --filter @taskboard/electron dev
```

**Production build:**
```bash
pnpm --filter @taskboard/electron build
pnpm --filter @taskboard/electron package
# Installers output to: packages/electron/release/
```

> `--path` points to the project root directory (the folder containing `taskops.db`).
> TaskBoard watches `taskops.db` and automatically refreshes when the DB changes.

→ [TaskBoard GitHub](https://github.com/godstale/TaskBoard)
