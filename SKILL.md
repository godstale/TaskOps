---
name: taskops
description: >
  Use when a project plan or implementation spec has been finalized and execution is about to begin,
  or a session starts on a project that already has a taskops.db.

  When starting work:
  - Register a workflow and import the full work plan (all tasks/epics) with workflow_id.
  - Before execution begins, register verifiable end-goals as Objectives (milestone = success criteria).
  - Also register in-execution constraints and cautions as Objectives (rules that must be followed during work).
  - When resuming an existing workflow, always check registered Objectives first to understand prior goals,
    constraints, and lessons learned before writing any code.

  During execution:
  - Record every tool/skill/sub-agent/MCP/plugin/thinking step to TaskOps via `op progress` with the
    appropriate flag: --tool, --skill, --mcp, --subagent. For thinking steps and plugin calls, use
    --summary "Thinking: [topic]" or --summary "Plugin: [name] — [action]".
  - Signal task start (`op start`) and completion (`op complete`) to keep Task status up to date.
  - When an error occurs, record it immediately via `op error --summary "..." --details "..."`.
    Errors are stored in the operations table (type='error') — there is no separate errors table.
  - Register resources (output files, memory files, config files) as they are created or modified,
    not only at session end.

  When work is complete:
  - Review each Objective: update status to 'done' or 'cancelled' to reflect actual outcomes.
  - Register a retrospective Objective summarizing: goal achievement results, what was lacking,
    what needs improvement, and what to remember or avoid in future sessions.
  - Register any new constraints, changed requirements, or cautions as Objectives for the next run.
  - Submit a workflow completion report via `workflow report`.

  When re-executing a workflow:
  - Always run `workflow restart <W-ID>` first — this resets all tasks to 'todo' AND clears the
    entire operations history (including error records) for a clean slate.
  - Register new Objectives capturing cautions, rule changes, or lessons from the previous run
    BEFORE starting execution.
---

# TaskOps — Project Management Skill for Claude Code

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
- TaskOps repository cloned (contains `cli/` package and `hooks/`)
- Project initialized with `python -m cli init`

---

## ⚠️ Common Mistakes (Gotchas)

These are the most frequent errors — check each before proceeding:

| Mistake | Fix |
|---------|-----|
| Missing `--workflow <W-ID>` on `epic create`, `task create`, `objective create` | Always pass `--workflow`; use `workflow import` for bulk creation |
| Using `epic create`/`task create` individually | `workflow import` is the **only valid plan registration path** |
| Not setting `TASKOPS_DB` env var | `export TASKOPS_DB=/absolute/path/to/project/taskops.db` first |
| Creating a new workflow without checking for duplicates | Always run `workflow list` before `workflow create` |
| Skipping resource registration before marking task done | `resource add <T-ID> --path ./file --type output --desc "..."` then verify: `resource list --task <T-ID>` must be non-empty |
| Not registering Objectives before execution starts | Before first task: `objective create --workflow <W-ID> --title "Goal" --milestone "Success criteria"` |
| Not doing post-work Objective review | After final task: `objective list --workflow <W-ID>`, update each status (done/cancelled), then register retrospective and next-run cautions as new Objectives |
| Not clearing operations when restarting workflow | `workflow restart <W-ID>` resets tasks to 'todo' AND clears all operations (including errors); no extra flag needed |
| Leaving a task `in_progress` when work stops | Always close with `op complete` or `task update --status interrupted` |

---

## Phase 1: Initialization

Initialize a new TaskOps project in the target directory.

```bash
python -m cli init --name "Project Name" --prefix PRJ --path ./project-path
```

This creates `taskops.db` (SQLite database).

After init, select an existing workflow or create a new one — **all ETS must belong to a workflow**:

```bash
# List existing workflows (resume scenario)
python -m cli workflow list

# Create a new workflow (always include --description for duplicate detection)
python -m cli workflow create \
  --title "My Plan" \
  --description "Brief description of scope and intent"
# → Workflow ID: PRJ-MP
```

### Configure Hooks

Register TaskOps hooks in `.claude/settings.json` (project-level):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|Bash|Agent",
        "command": "bash /path/to/TaskOps/hooks/on_tool_use.sh"
      }
    ]
  }
}
```

Available hooks:
- `on_task_start.sh <TASK_ID>` — Sets task to `in_progress`, records `op start`
- `on_tool_use.sh` — Records subagent dispatch as `op progress --subagent true` (Agent tool)
- `on_task_complete.sh <TASK_ID>` — Sets task to `done`, records `op complete`

---

## AI Agent Usage Scenarios

TaskOps persists work plans and artifacts across AI agent sessions. Use these patterns to store, retrieve, and re-execute workflows.

### Store a Plan for Later

Save a work plan as a workflow so any future session can pick it up:

```bash
# Create workflow with description (for duplicate detection)
python -m cli workflow create \
  --title "API Migration Plan" \
  --description "Migrate REST endpoints to async handlers. Covers auth, user, billing."
# → Workflow ID: PRJ-AMP

# Import the structured plan
python -m cli workflow import PRJ-AMP --structure '<json>'
```

### Resume a Plan in a New Session

At session start, check what workflows exist and load the relevant one:

```bash
# List all workflows
python -m cli workflow list

# Load full task structure for a workflow
python -m cli query show --workflow PRJ-AMP

# Find the next task to work on
python -m cli workflow next
```

### Track Artifacts Produced by a Workflow

Register files created during task execution as resources for later retrieval:

```bash
# Register an output file
python -m cli resource add AMP-T003 --path ./output/report.json --type output --desc "Final report"

# Register intermediate work product
python -m cli resource add AMP-T002 --path ./tmp/analysis.csv --type intermediate --desc "Raw analysis"

# Retrieve all artifacts from a workflow
python -m cli resource list --workflow PRJ-AMP

# Retrieve only final outputs
python -m cli resource list --workflow PRJ-AMP --type output
```

### Post-Work: Review Objectives and Register Results

After completing the final task, review every Objective and record outcomes:

```bash
# List all objectives for the workflow
python -m cli objective list --workflow PRJ-AMP

# Mark achieved objectives as done
python -m cli objective update PRJ-AMP-O001 --status done

# Mark objectives that were not achieved
python -m cli objective update PRJ-AMP-O002 --status cancelled

# Register a retrospective objective: what was achieved, what was lacking, what to improve
python -m cli objective create --workflow PRJ-AMP \
  --title "Retrospective: Login API implementation" \
  --milestone "Goals met: endpoints complete, tests pass. Issues: token refresh not implemented. Next: add refresh endpoint before auth epic is closed."

# Register cautions or rule changes for the next run as objectives
python -m cli objective create --workflow PRJ-AMP \
  --title "Next run: always verify DB path before op start" \
  --milestone "TASKOPS_DB must point to project root, not TaskOps repo root"

# Submit workflow completion report
python -m cli workflow report PRJ-AMP \
  --summary "Login API complete" \
  --details "All 5 endpoints implemented. JWT auth working. Refresh token deferred to next sprint."
```

### Re-execute a Workflow

Reset a workflow's tasks to `todo` and run it again. Other workflows are unaffected.
`workflow restart` clears **all operations and error records** for a clean slate.

```bash
# Step 1: Restart workflow (resets tasks + clears operations/errors)
python -m cli workflow restart PRJ-AMP

# Step 2: Register new objectives BEFORE starting execution
#   — cautions from previous run
python -m cli objective create --workflow PRJ-AMP \
  --title "Caution: skip workflow import if tasks already exist" \
  --milestone "workflow import deletes all existing tasks; check workflow list first"
#   — changed requirements
python -m cli objective create --workflow PRJ-AMP \
  --title "Changed: auth now uses OAuth2 instead of JWT" \
  --milestone "Update login endpoint to use OAuth2 flow per new spec"

# Step 3: Verify reset state
python -m cli query show --workflow PRJ-AMP
```

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

> ⚠️ `--workflow <W-ID>` is **required** for all create commands.

```bash
# Create Epics
python -m cli epic create --workflow PRJ-AMP --title "Authentication System"
# → AMP-E001

# Create Tasks under Epic
python -m cli task create --workflow PRJ-AMP --parent AMP-E001 --title "Login API"
# → AMP-T001

# Create SubTasks under Task (only when needed)
python -m cli task create --workflow PRJ-AMP --parent AMP-T001 --title "JWT token generation"
# → AMP-T002

# Create Objectives — verifiable end-goals (milestone = success criteria)
python -m cli objective create --workflow PRJ-AMP --title "MVP Complete" --milestone "All CRUD endpoints pass integration tests"
python -m cli objective create --workflow PRJ-AMP --title "Demo Day" --due-date 2026-04-01

# Create Objectives — in-execution constraints and cautions (rules to follow during work)
python -m cli objective create --workflow PRJ-AMP \
  --title "Constraint: No mock DB in tests" \
  --milestone "All tests hit real SQLite; mocks cause prod/test divergence"
python -m cli objective create --workflow PRJ-AMP \
  --title "Caution: workflow import replaces existing tasks" \
  --milestone "Always run workflow list before workflow import to avoid data loss"
```

### Define Workflow

```bash
# Set execution order
python -m cli workflow set-order AMP-T001 AMP-T002 AMP-T003

# Group tasks for parallel execution
python -m cli workflow set-parallel --group "auth-group" AMP-T002 AMP-T003

# Add dependencies
python -m cli workflow add-dep AMP-T004 --depends-on AMP-T002 AMP-T003
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
    {"type": "task", "title": "New Task", "parent_id": "AMP-E001"}
  ],
  "update": [{"id": "AMP-T001", "title": "...", "status": "..."}],
  "delete": [{"id": "AMP-T002"}]
}
```

Note: `parent_id` is **required** for `type: "task"` and must reference an existing epic or task. Any of `create`, `update`, `delete` may be omitted.

---

## Phase 3: Execution

Before starting work, **guide the user to launch TaskBoard** for real-time monitoring:

```bash
# In a separate terminal — run from the TaskBoard directory
pnpm --filter @taskboard/tui dev -- --path /path/to/project-root
```

> TaskBoard watches `taskops.db` and refreshes automatically as tasks progress.
> If TaskBoard is not installed, see the [Visualizing with TaskBoard](#visualizing-with-taskboard) section.

Work through tasks following the workflow order.

### Execution Reporting Obligations

These three behaviors are **required** during every execution session:

**1. Report sub-operations to TaskOps**

Hooks auto-record the following — no manual action needed:
- **Agent tool (subagent dispatch)** → recorded as `op progress --subagent true`

Record these **manually** with `op progress`:

```bash
# Tool used (Edit, Write, Bash, Read, ...)
python -m cli op progress <TASK_ID> --tool Edit --summary "Edited auth middleware"

# Skill invoked
python -m cli op progress <TASK_ID> --skill code-reviewer --summary "Skill: code-reviewer — reviewing AMP-T003"

# MCP server called
python -m cli op progress <TASK_ID> --mcp playwright --summary "MCP: playwright — navigated to /login for E2E test"

# Plugin called
python -m cli op progress <TASK_ID> --summary "Plugin: firecrawl — scraped https://example.com/docs"

# Thinking step (extended thinking or key reasoning)
python -m cli op progress <TASK_ID> --summary "Thinking: evaluated async vs sync handler trade-offs"

# Key decision or plan change
python -m cli op progress <TASK_ID> --summary "Decision: async handler over sync for auth endpoint"
```

**2. Signal task start and completion**

Always update Task status at the boundaries of each task (see commands below).
Never leave a task in `todo` while actively working on it, or in `in_progress` after it finishes.

**3. Register artifacts when all work is done**

After completing the final task in a session, register every meaningful output:

```bash
# Output files produced
python -m cli resource add <TASK_ID> --path ./path/to/output --type output --desc "description"

# Memory files — register immediately when written, not just at session end
python -m cli resource add <TASK_ID> --path ./.claude/memory/feedback_xyz.md --type output --desc "memory: feedback on testing approach"

# System/config files — register immediately when created or modified
python -m cli resource add <TASK_ID> --path ./.claude/settings.json --type output --desc "system: hooks configuration"
```

---

### Start a Task

```bash
# Check next executable task
python -m cli workflow next

# Start the task
python -m cli task update AMP-T001 --status in_progress
python -m cli op start AMP-T001 --platform claude_code
```

If hooks are configured, use `bash hooks/on_task_start.sh AMP-T001` instead.

### Record Progress

```bash
# Record meaningful progress milestones
python -m cli op progress AMP-T001 --summary "Implemented 3 of 5 endpoints"
```

With hooks configured, `on_tool_use.sh` records progress automatically on each tool use.

### Complete a Task

```bash
# Mark task as done
python -m cli task update AMP-T001 --status done
python -m cli op complete AMP-T001 --summary "Login API complete, all tests pass"
```

If hooks are configured, use `bash hooks/on_task_complete.sh AMP-T001` instead.

### Handle Interruptions

```bash
# Record interruption with reason
python -m cli task update AMP-T001 --status interrupted --interrupt "Waiting for API key"
python -m cli op interrupt AMP-T001 --summary "Blocked on external dependency"
```

### Handle Errors

Errors are recorded in the **operations table** (type=`error`) — there is no separate errors table.

```bash
# Record error with summary only
python -m cli op error AMP-T001 --summary "Database connection failed"

# Record error with full details (stack trace, context, etc.)
python -m cli op error AMP-T001 \
  --summary "SQLite constraint violation on task insert" \
  --details "UNIQUE constraint failed: tasks.id — duplicate ID AMP-T003 generated"
```

On workflow restart, all error records are cleared automatically along with operations.

---

## Phase 4: Monitoring

### Check Project Status

```bash
# Overall status with progress percentage
python -m cli query status

# List tasks by status
python -m cli query tasks --status in_progress

# View operation log for a task
python -m cli op log --task AMP-T001

# View full workflow
python -m cli workflow show
```

### Manage Resources

```bash
# Add resource reference to a task
python -m cli resource add AMP-T001 --path ./docs/spec.md --type input --desc "API spec"

# List resources
python -m cli resource list --task AMP-T001
```

### Manage Settings

```bash
python -m cli setting set commit_style "conventional" --workflow <W-ID> --desc "Commit message style"
python -m cli setting get commit_style --workflow <W-ID>
python -m cli setting list --workflow <W-ID>
```

---

## Reference: All CLI Commands

| Command | Description |
|---------|-------------|
| `init --name --prefix --path` | Initialize project |
| `epic create/list/show/update/delete` | Epic CRUD |
| `task create/list/show/update/delete` | Task/SubTask CRUD |
| `objective create/list/update/delete` | Objective CRUD |
| `plan update --changes <json>` | Update plan: create/update/delete tasks and epics |
| `workflow set-order/set-parallel/add-dep/show/next/current` | Workflow ordering and execution |
| `workflow restart <W-ID> [--clear-ops]` | Reset workflow tasks to todo for re-execution |
| `op start/progress/complete/error/interrupt/log` | Operations recording |
| `resource add/list [--task/--workflow/--type]` | Resource management |
| `query status/tasks/show` | Status queries and workflow details |
| `setting set/get/list/delete` | Settings management |

All commands use: `python -m cli [--db path] <command> <subcommand> [options]`

---

## Visualizing with TaskBoard

TaskBoard is a standalone read-only GUI that visualizes the TaskOps database. Guide the user to install it when they want to monitor project progress visually.

**Install**

```bash
git clone https://github.com/godstale/TaskBoard.git
cd TaskBoard
pnpm install
```

**Run**

```bash
# TUI (terminal)
pnpm --filter @taskboard/tui dev -- --path /path/to/taskops-root

# Electron (desktop app)
pnpm --filter @taskboard/electron dev
```

TaskBoard watches the `taskops.db` file and automatically refreshes when the DB changes.
→ [TaskBoard GitHub](https://github.com/godstale/TaskBoard)
