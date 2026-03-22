# TaskOps

TaskOps is a skill for AI Agents (Claude Code, Gemini CLI) that manages complex projects using ETS (Epic-Task-SubTask) structure.

## Project Status

- Phase: Released (v0.2.5)
- DB schema: `cli/db/schema.py`
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
  fragments/          # Shared instruction fragments
cli/                  # Python CLI tool
  taskops.py          # Entry point (argparse-based)
  db/                 # DB module (schema, connection)
  commands/           # Subcommand modules
  templates/          # MD file templates
hooks/                # Claude Code hooks
```

## Task ID System

- Epic: `{PREFIX}-E001`
- Task/SubTask: `{PREFIX}-T001` (same sequence, SubTask = Task with parent Task)
- Objective: `{PREFIX}-O001`

## Commands

All DB operations go through: `python cli/taskops.py <command> <subcommand> [options]`

Commands: `init`, `epic`, `task`, `objective`, `workflow`, `op`, `resource`, `query`, `setting`

## GIT commit rules

- Git commit 전에 불필요한 파일은 gitignore 에 추가하거나 삭제해야 한다.
- release 브랜치에 commit 하기 전에는 아래 파일들이 업데이트 되었는지 확인해야 한다.
  - `README.md`, `README.ko.md`, `CHANGELOG.md`
