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

## [0.2.5] - 2026-03-17

### Added

- `workflow create/list/delete` subcommands — manage named workflows
- `workflow import <W-ID> --structure/--structure-file` — bulk import TODO→ETS structure with replace semantics
- `workflow restart <W-ID> [--clear-ops]` — reset all tasks in a workflow to `todo`; auto-saves a checkpoint before restart; `--clear-ops` also removes operation history for that workflow
- `resource list --workflow <W-ID>` — filter resources by workflow scope (joins tasks on `workflow_id`); combinable with `--type`
- **AI Agent Usage Scenarios** section in `skills/taskops.md`, `skills/taskops-gemini.md`, and `SKILL.md` — cross-session patterns: store plan, resume in new session, track artifacts, re-execute workflow
- DB schema v3 — `workflows` table; `workflow_id` foreign key on `tasks`

### Changed

- `query generate-todo` renamed to `query show`; outputs to stdout only (no file write)
- `init` generates `TASKOPS.md` only; removed auto-generation of `AGENTS.md`, `SETTINGS.md`, and resource files
- Skill docs updated for v0.2.5: workflow import flow, `query show` usage, and scope rules

## [0.2.6] - 2026-03-22

### Added

- `workflow export <W-ID>` — generate a TODO.md snapshot of all tasks in a workflow to stdout
- `workflow create --description` — optional description field when creating a workflow
- `skills/fragments/planning-guide.md` — TaskOps-native planning guide (replaces `writing-plans` skill dependency)
- `skills/fragments/execution-guide.md` — TaskOps-native execution guide (replaces `executing-plans` skill dependency)
- `skills/fragments/setting-guide.md` — workflow dependency management reference
- DB schema v6 — `description` column on `workflows` table
- Workflow-scoped short ID prefix: epics, tasks, objectives, and plan imports now use the workflow prefix (e.g., `TW-E001`, `TW-T001`)
- `generate_workflow_short` / `get_workflow_prefix` utilities; `next_workflow_id` derives short prefix from workflow title
- Design docs: `docs/design/` workflow-first architecture spec and implementation plan

### Changed

- **DB-only principle**: `init` no longer generates `TASKOPS.md`; `setting` no longer generates `SETTINGS.md` — all state lives in the DB
- `skills/taskops.md` restructured to v0.2.6 slim + fragment-based layout; planning and execution guides are now self-contained fragments instead of delegating to external skills
- `SKILL.md`, `skills/taskops-gemini.md` updated to match v0.2.6 structure

### Fixed

- `workflow list` output now uses ASCII dash (`-`) instead of Unicode em-dash to avoid Windows cp949 encoding errors

### Removed

- `TASKOPS.md.tmpl` — no longer needed after DB-only principle adoption

## [0.2.7] - 2026-03-27

### Added

- `monitor` command — agent activity monitoring with four subcommands:
  - `monitor record` — record a single agent event (called by hooks)
  - `monitor parse` — parse a JSONL session file and import events into DB
  - `monitor report` — show tool usage report, filterable by workflow
  - `monitor summary` — show a per-session activity summary
- `hooks/on_session_end.sh` — Stop hook that auto-imports JSONL session events into `agent_events` on session end
- `skills/fragments/cli-reference.md` — dedicated CLI reference fragment (extracted from `SKILL.md` / `taskops.md` to reduce token cost)
- `docs/monitoring-guide.md` — detailed monitoring and agent-tracking guide

### Changed

- `SKILL.md` and `skills/taskops.md` — compacted and restructured; heavy CLI tables moved to `skills/fragments/cli-reference.md`; skill body now references fragments for planning, execution, monitoring, and CLI details
- `skills/fragments/monitoring-guide.md` — updated with `monitor` command usage and `agent_events` recording patterns
- `skills/fragments/execution-guide.md` — updated with correct agent info for operations table; improved step-by-step guidance
- `skills/fragments/planning-guide.md` and `setting-guide.md` — minor improvements for clarity
- `hooks/on_tool_use.sh` — updated to record `agent_events` via `monitor record`

### Fixed

- Operations table in `skills/fragments/execution-guide.md` and `monitoring-guide.md` — corrected invalid agent-platform field values

### Removed

- DB schema v7 `agent_events` table — added in v7 then dropped in v8 (monitoring moved to JSONL parse approach via `monitor parse`)

## [Unreleased]

- TBD
