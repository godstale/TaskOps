# TaskOps CLI Command Reference

All commands use: `python -m cli [--db PATH] <command> <subcommand> [options]`

The `--db` flag specifies the database path. If omitted, TaskOps looks for `taskops.db` in the current directory.

---

## `init` — Initialize Project

```bash
python -m cli init --name NAME --prefix PREFIX [--path PATH]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--name` | Yes | Project name |
| `--prefix` | Yes | ID prefix (e.g., `PRJ` → `PRJ-T001`) |
| `--path` | No | Target directory (default: current dir) |

Creates `taskops.db`, `TASKOPS.md`.

---

## `epic` — Epic Management

### `epic create`
```bash
python -m cli epic create --title TITLE [--desc DESC]
```

### `epic list`
```bash
python -m cli epic list
```

### `epic show`
```bash
python -m cli epic show EPIC_ID
```

### `epic update`
```bash
python -m cli epic update EPIC_ID [--title TITLE] [--desc DESC] [--status STATUS]
```
Status values: `todo`, `in_progress`, `done`, `interrupted`

### `epic delete`
```bash
python -m cli epic delete EPIC_ID
```

---

## `task` — Task and SubTask Management

Tasks and SubTasks share the same command and ID sequence (`PRJ-T001`, `PRJ-T002`, ...).
A Task with a Task parent becomes a SubTask.

### `task create`
```bash
python -m cli task create --parent PARENT_ID --title TITLE [--desc DESC]
```
`--parent` can be an Epic ID (creates Task) or Task ID (creates SubTask).

### `task list`
```bash
python -m cli task list [--epic EPIC_ID] [--status STATUS]
```

### `task show`
```bash
python -m cli task show TASK_ID
```

### `task update`
```bash
python -m cli task update TASK_ID [--title TITLE] [--desc DESC] [--status STATUS] [--interrupt REASON]
```
Use `--interrupt REASON` when setting status to `interrupted`.

### `task delete`
```bash
python -m cli task delete TASK_ID
```

---

## `objective` — Objective Management

Objectives track milestones and deadlines independently from ETS tasks.

### `objective create`
```bash
python -m cli objective create --title TITLE [--milestone DESC] [--due-date YYYY-MM-DD]
```
Use `--milestone` for milestone descriptions or `--due-date` for date-based deadlines.

### `objective list`
```bash
python -m cli objective list
```

### `objective update`
```bash
python -m cli objective update OBJ_ID [--title TITLE] [--milestone DESC] [--due-date DATE] [--status STATUS]
```
Status values: `pending`, `achieved`, `missed`

### `objective delete`
```bash
python -m cli objective delete OBJ_ID
```

---

## `plan update` — Bulk Plan Updates

When the user modifies the project plan (adds, removes, or renames tasks or epics), apply changes to the DB using a single command:

```bash
python -m cli plan update --changes '<json>'
```

### JSON Schema

The `--changes` parameter accepts a JSON object with up to three keys:

```json
{
  "create": [
    {"type": "epic", "title": "New Epic"},
    {"type": "epic", "title": "Another Epic", "desc": "Optional description"},
    {"type": "task", "title": "New Task", "parent_id": "PRJ-E001"},
    {"type": "task", "title": "SubTask", "parent_id": "PRJ-T001", "desc": "Optional"}
  ],
  "update": [
    {"id": "PRJ-T001", "title": "Updated Title"},
    {"id": "PRJ-E001", "title": "New Name", "status": "done"}
  ],
  "delete": [
    {"id": "PRJ-T002"},
    {"id": "PRJ-E003"}
  ]
}
```

### Requirements

- **`create`**: Array of objects with `type` ("epic" or "task"), `title`, optional `desc`
  - For `type: "task"`, `parent_id` is **required** and must reference an existing epic or task
  - For `type: "epic"`, `parent_id` is ignored
- **`update`**: Array of objects with `id` and any of `title`, `desc`, `status`
- **`delete`**: Array of objects with `id` only

### Notes

- Any of `create`, `update`, `delete` may be omitted
- IDs must match the pattern `PREFIX-T###` or `PREFIX-E###`
- Parent references must exist in the database before update

---

## `workflow` — Workflow Management

### `workflow set-order`
```bash
python -m cli workflow set-order TASK_ID [TASK_ID ...]
```
Assigns sequential `seq_order` values (1, 2, 3, ...) to the listed tasks.

### `workflow set-parallel`
```bash
python -m cli workflow set-parallel --group GROUP_NAME TASK_ID [TASK_ID ...]
```
Groups tasks for parallel execution. Tasks in the same group at the same `seq_order` run concurrently.

### `workflow add-dep`
```bash
python -m cli workflow add-dep TASK_ID --depends-on DEP_ID [DEP_ID ...]
```
Adds prerequisites — `TASK_ID` won't be `next` until all dependencies are `done`.

### `workflow show`
```bash
python -m cli workflow show
```
Shows full workflow with seq_order, groups, dependencies, and status.

### `workflow next`
```bash
python -m cli workflow next
```
Returns the next executable task(s) — `todo` tasks whose dependencies are all `done`.

### `workflow current`
```bash
python -m cli workflow current
```
Returns the currently `in_progress` task ID, if any.

---

## `op` — Operations Recording

Operations log the agent's actions on each task for auditing and progress tracking.

### `op start`
```bash
python -m cli op start TASK_ID --platform PLATFORM
```
Platform values: `claude_code`, `gemini_cli`, `manual`

### `op progress`
```bash
python -m cli op progress TASK_ID --summary SUMMARY [--subagent BOOL]
```

### `op complete`
```bash
python -m cli op complete TASK_ID --summary SUMMARY
```

### `op error`
```bash
python -m cli op error TASK_ID --summary SUMMARY
```

### `op interrupt`
```bash
python -m cli op interrupt TASK_ID --summary SUMMARY
```

### `op log`
```bash
python -m cli op log --task TASK_ID
```
Shows all operation records for a task in chronological order.

---

## `resource` — Resource Management

Resources link files or paths to specific tasks for tracking.

### `resource add`
```bash
python -m cli resource add TASK_ID --path FILE_PATH --type TYPE [--desc DESC]
```
Type values: `input`, `output`, `reference`

### `resource list`
```bash
python -m cli resource list [--task TASK_ID] [--type TYPE]
```

---

## `query` — Status Queries and Reports

### `query status`
```bash
python -m cli query status
```
Shows project-wide summary: total tasks, counts by status, progress percentage.

### `query tasks`
```bash
python -m cli query tasks [--status STATUS] [--epic EPIC_ID]
```

### `query show`
```bash
python -m cli query show [--workflow W_ID]
```
Shows full task structure. Use `--workflow` to filter by workflow.

---

## `setting` — Settings Management

### `setting set`
```bash
python -m cli setting set KEY VALUE [--desc DESC]
```

### `setting get`
```bash
python -m cli setting get KEY
```

### `setting list`
```bash
python -m cli setting list
```

### `setting delete`
```bash
python -m cli setting delete KEY
```

Settings are automatically synced to `SETTINGS.md` on each write.
