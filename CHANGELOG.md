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
- `TODO.md` auto-generation from DB state

**Tests**
- Unit tests for DB layer
- Integration tests for all commands and hook scripts

**Documentation**
- `README.md` with quick start guide
- `AGENTS.md` for Gemini CLI
- `CLAUDE.md` for Claude Code

---

## [0.2.0] - 2026-03-15

TaskOps skill-only release. TaskBoard GUI extracted to a separate repository.

### Added

- TaskBoard installation guide in `skills/taskops.md` and `skills/taskops-gemini.md`
  - Guides users to the standalone [TaskBoard](https://github.com/godstale/TaskBoard) repo for GUI visualization

### Removed

- `taskboard/` — entire TaskBoard GUI project (TUI + Electron) extracted to separate repo
- `docs/design/2026-03-15-taskops-design.md` — superseded by `docs/design/TASKOPS_DESIGN.md`
- `docs/plan/BUSINESS_LOGIC.md`, `docs/plan/IMPLEMENT_PLAN.md` — superseded by `docs/plan/TASKOPS_BUSINESS_LOGIC.md`, `docs/plan/TASKOPS_IMPLEMENT_PLAN.md`
- `docs/plans/` — temporary implementation plan artifacts

### Changed

- Project status updated to Released in `CLAUDE.md` and `AGENTS.md`

---

## [0.2.1] - 2026-03-15

### Added

- `SKILL.md` at repository root to support installation via `npx skills add godstale/TaskOps`
  - The `skills` npm package requires a file literally named `SKILL.md` with YAML frontmatter
  - Content mirrors `skills/taskops.md` (Claude Code skill)

---

## [0.2.2] - 2026-03-15

### Added

- `README.ko.md` — Korean translation of README, linked from `README.md`

### Changed

- `SKILL.md`, `skills/taskops.md`, `skills/taskops-gemini.md` — rewritten in English only (removed bilingual headers)
- `SKILL.md` / `skills/taskops.md` description updated to trigger automatic invocation: agent invokes TaskOps without explicit user instruction when a plan is finalized or a multi-step project starts
- `skills/taskops.md` / `skills/taskops-gemini.md` — added TaskBoard launch guidance at the start of Phase 3 (Execution)
- `AGENTS.md`, `CLAUDE.md` — rewritten in English only, version updated to v0.2.2
- `README.md` — rewritten in English only, added link to `README.ko.md`

---

## [0.2.3] - 2026-03-16

### Added

- `plan update` command — apply project plan changes (create/update/delete epics and tasks) to the DB atomically via JSON input
- Extended operation metadata: `tool_name`, `skill_name`, `mcp_name`, `retry_count`, `input_tokens`, `output_tokens`, `duration_seconds` fields on operations
- DB schema migration system (v1 → v2)

### Removed

- `query generate-ops` subcommand and `TASK_OPERATIONS.md` auto-generation — use `op log` to query operation history from DB

## [0.2.4] - 2026-03-16

### Added

- `skills/taskops.md` — **Scope & File Safety Rules** section: explicitly prohibits destructive file-system operations (rm, rmdir, del, etc.) based on TaskOps commands; TaskOps manages task data only
- `skills/taskops.md` — **Handling Reset Requests** section: when user asks to "reset" or "initialize", agent must present two explicit options (reset status only vs. delete plan) and wait for selection before acting
- `docs/superpowers/` — internal planning and spec documents for v0.2.3 feature development

## [Unreleased]

- TBD
