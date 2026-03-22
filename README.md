# TaskOps

**AI Agent Project Management Skill** — Manage complex projects using ETS (Epic-Task-SubTask) structure with SQLite-backed tracking, workflow management, and operations monitoring.

Supports **Claude Code** (with hooks) and **Gemini CLI** (explicit recording).

> 한국어 문서: [README.ko.md](README.ko.md)

---

## What It Does

TaskOps gives AI Agents a structured way to manage multi-step projects across sessions:

- **ETS Hierarchy**: Decompose projects into Epics → Tasks → SubTasks
- **Workflow Engine**: Sequential and parallel execution with dependency tracking
- **Operations Log**: Record start/progress/complete/error/interrupt events per task, with automatic workflow association
- **Query & Reports**: View project status, task lists, and workflow details
- **Resource Tracking**: Link files to tasks with automatic workflow association
- **Settings Store**: Key-value config synced to `SETTINGS.md`
- **Visual Monitoring**: Use [TaskBoard](https://github.com/godstale/TaskBoard) to view project status in a live GUI (TUI or Electron desktop app)

## Quick Start

```bash
git clone https://github.com/godstale/TaskOps.git
cd my-project

# Initialize TaskOps in your project
python -m cli init --name "My Project" --prefix MYP --path .

# Create or select a workflow (required before any ETS creation)
python -m cli workflow create --title "My Plan"
# → Workflow ID: MYP-W001

# Plan: create epics and tasks (--workflow required)
python -m cli epic create --workflow MYP-W001 --title "Core Feature"
python -m cli task create --workflow MYP-W001 --parent MYP-E001 --title "Implement API"

# Set workflow order
python -m cli workflow set-order MYP-T001

# Execute
python -m cli workflow next          # -> MYP-T001
python -m cli task update MYP-T001 --status in_progress
python -m cli op start MYP-T001 --platform claude_code
# ... do the work ...
python -m cli task update MYP-T001 --status done
python -m cli op complete MYP-T001 --summary "API complete"
```

See [docs/usage/quickstart.md](docs/usage/quickstart.md) for the full guide.

## Monitoring with TaskBoard

[TaskBoard](https://github.com/godstale/TaskBoard) is a companion GUI that reads the TaskOps SQLite database in real-time and displays your project status visually. It runs as a **terminal UI (TUI)** or a **desktop Electron app**, and automatically refreshes whenever the DB changes.

```bash
git clone https://github.com/godstale/TaskBoard.git
cd TaskBoard
pnpm install

# TUI (terminal)
pnpm --filter @taskboard/tui dev -- --path /path/to/your-project

# Electron (desktop)
pnpm --filter @taskboard/electron dev
```

TaskBoard is read-only — it never writes to the TaskOps DB. Use it to monitor progress in real-time while the AI Agent works.

---

## Using as a Skill

### Claude Code

Add `skills/taskops.md` as a Claude Code skill via `npx skills add godstale/TaskOps`, or manually copy `SKILL.md` to your skills directory.

The skill is designed to be **invoked automatically** — the AI Agent will start TaskOps without an explicit user instruction whenever a plan is finalized and execution is about to begin.

Configure hooks in `.claude/settings.json` to auto-record operations:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|Bash",
        "command": "bash /path/to/TaskOps/hooks/on_tool_use.sh"
      }
    ]
  }
}
```

### Gemini CLI

Use `skills/taskops-gemini.md`. Gemini CLI has no hooks — the skill instructs the agent to call `op` commands explicitly at each step.

## Project Structure

```
TaskOps/
├── SKILL.md                 # Root skill file (for npx skills add)
├── cli/                     # Python CLI package
│   ├── __main__.py          # Entry point: python -m cli
│   ├── taskops.py           # argparse routing
│   ├── db/                  # DB layer (schema, connection)
│   ├── commands/            # Subcommand modules
│   └── templates/           # MD file templates
├── hooks/                   # Claude Code hook scripts
│   ├── on_task_start.sh
│   ├── on_task_complete.sh
│   └── on_tool_use.sh
├── skills/                  # AI Agent skill documents
│   ├── taskops.md           # Claude Code skill
│   ├── taskops-gemini.md    # Gemini CLI skill
│   └── fragments/           # Shared instruction fragments
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
└── docs/usage/              # Documentation
```

## CLI Reference

See [docs/usage/commands.md](docs/usage/commands.md) for the full command reference.

| Command | Description |
|---------|-------------|
| `init --name --prefix --path` | Initialize project |
| `epic create/list/show/update/delete` | Epic CRUD |
| `task create/list/show/update/delete` | Task/SubTask CRUD |
| `objective create/list/update/delete` | Objective CRUD |
| `workflow set-order/set-parallel/add-dep/show/next/current` | Workflow management |
| `workflow restart <W-ID> [--clear-ops]` | Reset workflow tasks to todo for re-execution |
| `op start/progress/complete/error/interrupt/log` | Operations recording (auto-sets workflow_id) |
| `op log [--task/--workflow]` | View operation log with optional filters |
| `resource add/list [--task/--workflow/--type]` | Resource management (auto-sets workflow_id) |
| `query status/tasks/show` | Status queries and workflow details |
| `setting set/get/list/delete` | Settings management |

## Requirements

- Python 3.10+
- No external dependencies (stdlib only: `sqlite3`, `argparse`, `json`, `string`)

## Testing

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests (requires bash)
python -m pytest tests/integration/ -v

# Full suite
python -m pytest tests/ -v
```
