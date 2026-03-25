---
name: taskops
description: >
  Use when ANY of these is true:
  - when a project plan or implementation spec has been finalized and execution is about to begin
  - Session starts and `taskops.db` exists in the project directory (resume mode)

  When starting work:
  - Create a workflow to register the work plan.
  - Register the workflow's goals as Objectives BEFORE execution begins.

  During execution:
  - Signal task start (`op start`) and completion (`op complete`) for every task.
  - Register all output artifacts as resources before marking a task done.

  When work is complete:
  - Review each Objective and verify whether it was achieved.
  - Register a new Objective summarizing: what was lacking, what needs improvement,
    and what to remember or avoid in future sessions performing similar work.
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

## ⚠️ Common Mistakes (Gotchas)

These are the most frequent errors — check each before proceeding:

| Mistake | What happens | Fix |
|---------|-------------|-----|
| Missing `--workflow <W-ID>` on `epic create`, `task create`, `objective create` | Command fails or creates orphaned record | Always pass `--workflow`; use `workflow import` for bulk creation |
| Using `epic create`/`task create` individually instead of `workflow import` | Inconsistent plan state, no execution order | `workflow import` is the **only valid plan registration path** |
| Not setting `TASKOPS_DB` env var | Commands operate on wrong or default DB | Always `export TASKOPS_DB=/absolute/path/to/project/taskops.db` first |
| Creating a new workflow without checking for duplicates | Duplicate workflows tracking same work | Always run `workflow list` before `workflow create` |
| Skipping resource registration before `task update --status done` | Artifacts lost, gate violation | `resource add <T-ID> --path ./file --type output --desc "..."` then `resource list --task <T-ID>` — must be non-empty before marking done |
| Not registering Objectives before execution starts | Goals not tracked; no retrospective anchor | Before first task: `objective create --workflow <W-ID> --title "Goal" --milestone "Success criteria"` |
| Not doing post-work Objective review | Lessons not captured for future sessions | After final task: `objective list --workflow <W-ID>`, then: `objective create --workflow <W-ID> --title "Retrospective: ..." --milestone "what went well, what was lacking, what to avoid"` |
| Not clearing operations when restarting workflow | Stale operation history misleads future sessions | `workflow restart <W-ID>` always clears operations automatically — no extra flag needed |
| Leaving a task `in_progress` when work stops | Inconsistent DB state on resume | Always close with `op complete` or `task update --status interrupted` |

---

## ⛔ File Safety Rule

**TaskOps manages ONLY `taskops.db`.** Do NOT create, modify, or delete any other files as part of a TaskOps operation. This means: no source files, no README, no CLAUDE.md, no TODO.md, no SETTINGS.md.

Exception: `workflow export` may create a TODO.md file **only when the user explicitly requests it**.

---

## Handling Reset Requests

When user asks to "reset" or "start over", always ask which type:

> **Option 1 — 상태만 초기화 (Keep plan, reset status)**
> `python -m cli workflow restart {PREFIX}-{SHORT}`
>
> **Option 2 — 계획부터 다시 시작 (Delete plan, re-plan)**
> `python -m cli workflow delete {PREFIX}-{SHORT}` → re-run planning phase

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

# 3. Select or create a workflow — ALL ETS require a workflow_id
#    List existing (resume scenario):
python -m cli workflow list
#    Check for existing workflows first (duplicate detection):
python -m cli workflow list
#    Create new (always include --description):
python -m cli workflow create \
  --title "My Plan" \
  --description "Brief description of scope and intent"
# → Workflow ID: PRJ-MP
```

> ⚠️ Step 3 is mandatory. All Epics, Tasks, and Objectives must belong to a workflow. The `epic create`, `task create`, and `objective create` commands require `--workflow <W-ID>`.

Hook configuration (optional):
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

> Hook guard: `on_tool_use.sh` only fires when `TASKOPS_ACTIVE=1`.
> Agent tool fires subagent dispatch recording; Edit/Write/Bash record to `agent_events` only.

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
1. `op start {T-ID}` → set task status to `in_progress` → do the work → `op progress {T-ID}` (at milestones)
2. ⛔ **RESOURCE GATE** — register EVERY output file before marking done:
   ```bash
   python -m cli resource add {T-ID} --path ./path/to/output.py --type output --desc "What this file is"
   python -m cli resource list --task {T-ID}   # must show at least 1 entry
   ```
3. `task update {T-ID} --status done` → `op complete {T-ID} --summary "..."`
4. Parent epic status is auto-updated (no manual `epic update` needed)

**After ALL tasks in the workflow are done, submit a final report:**
```bash
python -m cli workflow report {PREFIX}-{SHORT} \
  --summary "One-sentence summary of what was accomplished" \
  --details "Full markdown report: what was built, key decisions, files created"
```

For operations recording detail, see `@skills/fragments/monitoring-guide.md`.

---

## Phase 4: Monitoring

```bash
python -m cli query status --workflow {PREFIX}-{SHORT}
python -m cli query show --workflow {PREFIX}-{SHORT}
python -m cli op log --workflow {PREFIX}-{SHORT}
python -m cli workflow next --workflow {PREFIX}-{SHORT}
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

# Reset specific workflow tasks to todo (operations always cleared automatically)
python -m cli workflow restart {PREFIX}-{SHORT}

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
python -m cli query show --workflow {PREFIX}-{SHORT}

# Find the next task
python -m cli workflow next --workflow {PREFIX}-{SHORT}
```

---

## Reference: All CLI Commands

| Command | Description |
|---------|-------------|
| `init --name --prefix [--path]` | Initialize project (creates taskops.db only) |
| `workflow create --title --description` | Create a workflow; `--description` sets scope for duplicate detection |
| `workflow list` | List all workflows |
| `workflow import <W-ID> --structure '<json>'` | Import full ETS plan (required path) |
| `workflow import <W-ID> --structure-file <path>` | Import from JSON file |
| `workflow export <W-ID> [--output <path>]` | Export to TODO.md (default: next to DB) |
| `workflow report <W-ID> --summary '...' [--details '...']` | Submit final completion report; marks workflow completed |
| `workflow delete <W-ID>` | Delete workflow and all its tasks |
| `workflow restart <W-ID>` | Reset workflow tasks to todo; operations always cleared |
| `workflow show [--workflow <W-ID>]` | Show execution order |
| `workflow next [--workflow <W-ID>]` | Show next executable tasks |
| `workflow current [--workflow <W-ID>]` | Show active task |
| `workflow set-order <T-ID>...` | Set sequential execution order |
| `workflow set-parallel --group <name> <T-ID>...` | Group for parallel execution |
| `workflow add-dep <T-ID> --depends-on <T-ID>...` | Add task dependency |
| `epic create --title --workflow <W-ID>` | Create epic (workflow required) |
| `epic list/show/update/delete` | Epic management |
| `task create --parent --title --workflow <W-ID>` | Create task (workflow required) |
| `task list [--epic] [--status] [--workflow <W-ID>]` | List tasks |
| `task show/update/delete` | Task management |
| `task update <T-ID> --status <status>` | Status: todo\|in_progress\|interrupted\|done\|cancelled |
| `objective create --title --workflow <W-ID>` | Create milestone marker (workflow required) |
| `objective list/update/delete` | Objective management |
| `plan update --changes '<json>' [--workflow <W-ID>]` | Partial plan changes (--workflow required if creates present) |
| `op start/progress/complete/error/interrupt <T-ID>` | Record operation (workflow_id auto-resolved) |
| `op log [--task <T-ID>] [--workflow <W-ID>]` | View operation history |
| `resource add <T-ID> --path --type --desc` | Register artifact (workflow_id auto-resolved) |
| `resource list [--task <T-ID>] [--workflow <W-ID>] [--type]` | List artifacts |
| `query show [--workflow <W-ID>]` | Full task tree view |
| `query status [--workflow <W-ID>]` | Progress summary |
| `query tasks [--status] [--workflow <W-ID>]` | Filtered task list |
| `setting set <key> <val> --workflow <W-ID> [--desc '...']` | Set workflow-scoped setting (**--workflow required**) |
| `setting get <key> --workflow <W-ID>` | Get setting value (**--workflow required**) |
| `setting list [--workflow <W-ID>]` | List settings (all if --workflow omitted) |
| `setting delete <key> --workflow <W-ID>` | Delete setting (**--workflow required**) |
| `project checkpoint [--note]` | Create status snapshot |
| `project checkpoint list` | List snapshots |
| `project rollback --checkpoint <id>` | Restore task statuses from snapshot |
| `project restart [--clear-ops]` | Reset all tasks to todo |

**workflow_id rules:**

| How task is created | workflow_id |
|---------------------|-------------|
| `workflow import` | ✅ Set automatically |
| `epic/task/objective create` | ❗ `--workflow <W-ID>` required |
| `plan update` with creates | ❗ `--workflow <W-ID>` required (or per-item `workflow_id` in JSON) |
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
