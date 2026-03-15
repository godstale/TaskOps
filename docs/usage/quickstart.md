# TaskOps Quick Start Guide

## Overview

TaskOps is a project management tool for AI Agents. It decomposes complex projects into an ETS (Epic-Task-SubTask) hierarchy, tracks progress via SQLite, and provides workflow management with dependency resolution.

## Prerequisites

- Python 3.10+
- Git (to clone the repository)

## Installation

```bash
git clone https://github.com/godstale/TaskOps.git
cd TaskOps
```

No additional packages are required — TaskOps uses Python's standard library only (`sqlite3`, `argparse`, `json`).

## Step 1: Initialize a Project

Run `init` in your project directory:

```bash
python -m cli init --name "My Project" --prefix MYP --path ./my-project
cd my-project
```

This creates:

| File | Purpose |
|------|---------|
| `taskops.db` | SQLite database (all project data) |
| `TODO.md` | Auto-generated task overview |
| `AGENTS.md` | AI Agent instructions |
| `SETTINGS.md` | Project settings |
| `resources/` | Resource file directory |

## Step 2: Plan with ETS Structure

Decompose your project into Epics → Tasks → SubTasks:

```bash
# Create an Epic (major feature)
python -m cli epic create --title "User Authentication"

# Create Tasks under the Epic
python -m cli task create --parent MYP-E001 --title "Login API"
python -m cli task create --parent MYP-E001 --title "Session Management"

# Create SubTasks (optional, for detailed breakdown)
python -m cli task create --parent MYP-T001 --title "JWT token generation"
```

Set up milestones with Objectives:

```bash
python -m cli objective create --title "MVP Complete" --milestone "Core auth done"
python -m cli objective create --title "Launch" --due-date 2026-06-01
```

## Step 3: Define Workflow

```bash
# Set execution order
python -m cli workflow set-order MYP-T001 MYP-T002

# Group tasks to run in parallel
python -m cli workflow set-parallel --group "auth-core" MYP-T001 MYP-T002

# Add dependencies
python -m cli workflow add-dep MYP-T003 --depends-on MYP-T001 MYP-T002

# Generate TODO.md
python -m cli query generate-todo
```

## Step 4: Execute Tasks

```bash
# Check what to work on next
python -m cli workflow next

# Start working on a task
python -m cli task update MYP-T001 --status in_progress
python -m cli op start MYP-T001 --platform claude_code

# Record progress milestones
python -m cli op progress MYP-T001 --summary "Implemented 3 of 5 endpoints"

# Complete a task
python -m cli task update MYP-T001 --status done
python -m cli op complete MYP-T001 --summary "Login API complete, all tests pass"
python -m cli query generate-todo
```

## Step 5: Monitor Progress

```bash
# Overall project status
python -m cli query status

# Filter tasks by status
python -m cli query tasks --status in_progress

# View operation log
python -m cli op log --task MYP-T001
```

## Using with Claude Code (Hooks)

Register hooks in `.claude/settings.json` at your project root:

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

Then use hook scripts for task lifecycle:

```bash
bash /path/to/TaskOps/hooks/on_task_start.sh MYP-T001
# ... do your work ...
bash /path/to/TaskOps/hooks/on_task_complete.sh MYP-T001
```

## Using as a Claude Code Skill

Add `skills/taskops.md` as a skill in your Claude Code configuration, then invoke it with:

```
/taskops
```

Claude will guide you through initialization, planning, and execution.

## Using with Gemini CLI

See `skills/taskops-gemini.md` for the Gemini CLI version. The key difference: Gemini CLI has no hooks, so all `op` commands must be called explicitly.
