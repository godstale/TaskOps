# Changelog

All notable changes to TaskOps are documented here.

Format: `[version] YYYY-MM-DD`

---

## [0.1.0] - 2026-03-15

Initial release of TaskOps — AI Agent project management skill.

### Added

**Core Infrastructure**
- DB schema and connection modules (`cli/db/`)
- CLI entry point with argparse (`cli/taskops.py`) and all command stubs

**Commands**
- `init` — initialize TaskOps in a project directory
- `epic` — create, update, list, and delete Epics
- `task` — create, update, list, delete Tasks and SubTasks (ETS hierarchy)
- `objective` — define and track project objectives
- `workflow` — sequential/parallel execution with dependency tracking
- `op` (operation) — log start/progress/complete/error/interrupt events per task
- `resource` — link files and URLs to tasks
- `query` — cross-entity search and filtering
- `setting` — key-value config store synced to `SETTINGS.md`

**Skill Documents**
- `skills/taskops.md` — Claude Code skill
- `skills/taskops-gemini.md` — Gemini CLI skill
- `skills/fragments/` — shared instruction fragments

**Hooks**
- Claude Code hooks for auto-recording operations and generating reports
- `TODO.md` and `TASK_OPERATIONS.md` auto-generation from DB state

**Tests**
- Unit tests for DB layer
- Integration tests for all commands and hook scripts

**Documentation**
- `README.md` with quick start guide
- `AGENTS.md` for Gemini CLI
- `CLAUDE.md` for Claude Code

---

## [Unreleased]

- TBD
