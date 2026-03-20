# TaskOps

TaskOps is a skill for AI Agents (Claude Code, Gemini CLI) that manages complex projects using ETS (Epic-Task-SubTask) structure.

## Project Status

- Phase: Released (v0.2.5)
- DB schema: `docs/DB_SCHEMA.md`
- Skill documents: `SKILL.md`
- Readme: `README.md`

## Architecture

- **Approach**: Skill-First — Skill documents (.md) are the primary entry point; Agents read and follow instructions to call Python CLI
- **Target Platforms**: Claude Code + Gemini CLI
- **DB**: SQLite via Python built-in `sqlite3` module
- **Distribution**: Git repository based

## Key Files

```
skills/               # Skill documents (Agent reads these)
  taskops.md          # Claude Code skill
  taskops-gemini.md   # Gemini CLI skill
  fragments/          # Shared instruction fragments
cli/                  # Python CLI tool
  taskops.py          # Entry point (argparse-based)
  db/                 # DB module (schema, connection)
  commands/           # Subcommand modules
  templates/          # MD file templates
hooks/                # Claude Code hooks
docs/                 # Documentation
  plan/               # Business logic & implementation plan
  design/             # Design documents
```

## Task ID System

- Epic: `{PREFIX}-E001`
- Task/SubTask: `{PREFIX}-T001` (same sequence, SubTask = Task with parent Task)
- Objective: `{PREFIX}-O001`

## Commands

All DB operations go through: `python cli/taskops.py <command> <subcommand> [options]`

Commands: `init`, `epic`, `task`, `objective`, `workflow`, `op`, `resource`, `query`, `setting`
