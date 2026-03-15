# TaskOps

TaskOps is a skill for AI Agents (Claude Code, Gemini CLI) that manages complex projects using ETS (Epic-Task-SubTask) structure.
TaskOps는 AI Agent용 프로젝트 관리 skill로, 복잡한 프로젝트를 ETS 구조로 분해하여 관리합니다.

## Project Status

- Phase: Design (설계 완료, 구현 대기)
- Design Doc: `docs/design/2026-03-15-taskops-design.md`

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
