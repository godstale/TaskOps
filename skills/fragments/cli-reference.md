# TaskOps CLI Reference

All commands: `python -m cli <command> <subcommand> [options]`
Env required: `export TASKOPS_DB=/abs/path/taskops.db`

## Project Init

```bash
python -m cli init --name "Name" --prefix PRJ    # creates taskops.db
```

## Workflow

```bash
python -m cli workflow list                                         # list all (check duplicates first)
python -m cli workflow create --title "..." --description "..."    # create (--description required)
python -m cli workflow import <W-ID> --structure '<json>'          # import ETS plan (only valid path)
python -m cli workflow import <W-ID> --structure-file <path>
python -m cli workflow export <W-ID> [--output TODO.md]            # export to file
python -m cli workflow report <W-ID> --summary "..." [--details "..."]  # mark complete
python -m cli workflow restart <W-ID>                              # reset tasks + clear ops
python -m cli workflow delete <W-ID>
python -m cli plan update --changes '<json>' [--workflow <W-ID>]  # partial changes (create/update/delete)
```

## Workflow Ordering

```bash
python -m cli workflow set-order <T-ID> <T-ID> ...            # sequential order
python -m cli workflow set-parallel --group <name> <T-ID> ... # parallel group
python -m cli workflow add-dep <T-ID> --depends-on <T-ID> ... # add dependency
python -m cli workflow show [--workflow <W-ID>]               # view full order
python -m cli workflow next [--workflow <W-ID>]               # next executable task(s)
python -m cli workflow current [--workflow <W-ID>]            # active task
```

→ Ordering model: `@skills/fragments/workflow-guide.md`

## ETS (Epic / Task / Objective)

> ⚠️ All create commands require `--workflow <W-ID>`. Use `workflow import` for bulk creation.

```bash
python -m cli epic create --title "..." --workflow <W-ID>
python -m cli epic list/show/update/delete

python -m cli task create --title "..." --parent <ID> --workflow <W-ID>
python -m cli task list [--epic <E-ID>] [--status <status>] [--workflow <W-ID>]
python -m cli task show/delete
python -m cli task update <T-ID> --status todo|in_progress|interrupted|done|cancelled

python -m cli objective create --title "..." --workflow <W-ID> [--milestone "..."] [--due-date YYYY-MM-DD]
python -m cli objective list/update/delete
```

`plan update` JSON format:
```json
{
  "create": [{"type": "epic", "title": "..."}, {"type": "task", "title": "...", "parent_id": "<E-ID>"}],
  "update": [{"id": "<T-ID>", "title": "..."}],
  "delete": [{"id": "<T-ID>"}]
}
```

→ ETS rules: `@skills/fragments/ets-planning.md`

## Operations

```bash
python -m cli op start <T-ID> --platform claude_code|gemini|unknown
python -m cli op progress <T-ID> --summary "..." [--subagent true]
python -m cli op complete <T-ID> --summary "..."
python -m cli op error <T-ID> --summary "..." [--details "..."]
python -m cli op interrupt <T-ID> --summary "..."
python -m cli op log [--task <T-ID>] [--workflow <W-ID>]
```

→ When to record each type: `@skills/fragments/monitoring-guide.md`

## Resources

```bash
python -m cli resource add <T-ID> --path <path> --type input|output|intermediate|reference --desc "..."
python -m cli resource list [--task <T-ID>] [--workflow <W-ID>] [--type <type>]
```

## Query & Status

```bash
python -m cli query status [--workflow <W-ID>]           # progress summary
python -m cli query show [--workflow <W-ID>]             # full task tree
python -m cli query tasks [--status <status>] [--workflow <W-ID>]
```

## Settings

> ⚠️ `--workflow` is required for `set`, `get`, `delete`.

```bash
python -m cli setting set <key> <value> --workflow <W-ID> [--desc "..."]
python -m cli setting get <key> --workflow <W-ID>
python -m cli setting list [--workflow <W-ID>]
python -m cli setting delete <key> --workflow <W-ID>
```

→ Built-in settings & patterns: `@skills/fragments/setting-guide.md`
