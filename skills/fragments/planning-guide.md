# Planning Guide / TaskOps 계획 수립 가이드

> TaskOps replaces `writing-plans`. Plans are stored in the TaskOps DB — no `.md` plan file is created. The DB IS the plan.

## Step 1: Announce

> "I'm using TaskOps to plan and track this project."

## Step 2: Scope Check

If the spec covers 2+ independent subsystems that could be completed separately:
- Create a separate workflow per subsystem
- Each workflow is independently executable and trackable

If all work is one cohesive feature → single workflow.

## Step 2.5: Duplicate Workflow Pre-Check

Before creating a new workflow, **always** check for existing ones:

```bash
python -m cli workflow list
```

Read each workflow's title and description:
- If a workflow with the same or very similar scope exists → resume it (`workflow restart`) instead of creating a new one
- If no matching workflow found → proceed to create a new one

## Step 3: ETS Structure Design

Design before converting to JSON:

```
Workflow — Container for all work (the "plan")
  └── Epic — Major feature area (non-executable; groups Tasks)
        └── Task — One executable unit (completable in one session)
              └── Task — Sub-step (same type; parent is a Task, not Epic)
  └── Objective — Milestone/deadline marker (non-executable; use sparingly)
```

**Decomposition rules:**
- Epic: 3–10 Tasks. Cannot be started or completed directly. Container only.
- Task: Clear done-condition. One agent session. Can have child Tasks.
- SubTask (= Task): Use only when a Task has distinct independently-verifiable steps.
- Objective: Use for time-based goals or milestones. Not part of execution sequence.

## Step 4: Convert to JSON and Import

**Required init sequence (do not skip steps):**

```bash
# 1. Set DB path
export TASKOPS_DB=/absolute/path/to/project/taskops.db
export TASKOPS_ACTIVE=1

# 2. Initialize (creates taskops.db only)
python -m cli init --name "Project Name" --prefix PRJ

# 3. Check for existing workflows (duplicate detection — always run this first)
python -m cli workflow list
#    If a similar workflow exists → resume it; otherwise create new:
python -m cli workflow create \
  --title "Plan Title" \
  --description "Detailed scope: what will be built, what modules affected, key constraints."
# → Note the workflow ID: PRJ-PT

# 4. Import full ETS structure in one call
python -m cli workflow import PRJ-PT --structure '<json>'
```

> ⚠️ **workflow_id is required for all ETS.** After `init`, you MUST either select an existing workflow or create a new one before creating any Epics, Tasks, or Objectives. All create commands (`epic create`, `task create`, `objective create`) require `--workflow <W-ID>`. Workflow IDs use a title-derived short string (e.g., `PRJ-PT` for "Plan Title").

JSON format:
```json
{
  "epics": [
    {
      "title": "Epic title",
      "description": "optional",
      "tasks": [
        {
          "title": "Task title",
          "description": "optional",
          "tasks": [{"title": "SubTask title"}],
          "resources": [{"path": "./output.html", "type": "output", "desc": "..."}]
        }
      ]
    }
  ]
}
```

> ⛔ NEVER use `epic create` / `task create` individually. `workflow import` is the only valid plan registration path.

## Step 5: Register Objectives

Before execution, register the workflow's goals as Objectives. These serve as the anchor for the post-work retrospective.

```bash
# Goal-based objective (what success looks like)
python -m cli objective create --workflow PRJ-PT \
  --title "All API endpoints migrated and tested" \
  --milestone "REST → async migration complete"

# Deadline-based objective
python -m cli objective create --workflow PRJ-PT \
  --title "Demo-ready build" --due-date 2026-04-01
```

> ⛔ Objectives must be registered **before starting the first task**. Verify with: `python -m cli objective list --workflow PRJ-PT`

## Step 6: Configure Settings (Dependencies)

Before execution, register any required tools, services, or APIs as settings.
**Always specify `--workflow` so settings are scoped to this plan:**

```bash
# --workflow is required for all setting commands
python -m cli setting set docker_required true --workflow PRJ-PT --desc "Docker CLI needed for build tasks"
python -m cli setting set openai_api_configured false --workflow PRJ-PT --desc "Needs API key before Task T003"
```

Verify:
```bash
python -m cli setting list --workflow PRJ-PT
```

See `@skills/fragments/setting-guide.md` for full setting reference.

## Step 7: Verify and Show Plan

```bash
python -m cli query show --workflow PRJ-PT
python -m cli setting list --workflow PRJ-PT
```

## Planning Gate

After plan is verified, ALWAYS ask before proceeding to execution:

> "계획이 완성되었습니다. 실행을 시작하기 전에 TaskOps로 작업을 관리하시겠습니까?
> TaskOps를 사용하면 진행 상황을 추적하고, 이후 세션에서도 이어서 작업할 수 있습니다."

- **User agrees** → proceed to Execution Phase (`@skills/fragments/execution-guide.md`)
- **User declines** → use `writing-plans` + `executing-plans` instead. Do not invoke TaskOps further.

> ⚠️ Once user chooses TaskOps, do NOT invoke `writing-plans`, `executing-plans`, or `subagent-driven-development`. They use incompatible tracking (TodoWrite vs. SQLite).

## Export to TODO.md (On Request)

If the user wants a file snapshot of the plan at any time:

```bash
python -m cli workflow export PRJ-PT [--output TODO.md]
```
