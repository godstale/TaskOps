# TaskBoard Integration & Rollback Support — Design Spec

> Date: 2026-03-15
> Status: Approved

---

## 1. Overview

This spec covers two additions to the TaskOps skill:

1. **TaskBoard Integration** — Auto-detect, install, and launch TaskBoard (TUI or Electron) from within the `taskops.md` skill. Include full manual usage instructions for both modes.
2. **Rollback & Restart** — Add three rollback mechanisms: per-task status rollback, checkpoint-based project rollback, and full project restart.

---

## 2. Design Decisions

| # | Item | Decision |
|---|------|----------|
| 1 | Approach | Approach A — extend `taskops.md` skill + add CLI subcommands |
| 2 | TaskBoard path | `--path` points to project root (where `taskops.db` lives), not parent directory |
| 3 | TaskBoard detection | Check `~/TaskBoard`, `./TaskBoard`, `TASKBOARD_PATH` env var in that order |
| 4 | TUI default | TUI is the default recommendation (stable); Electron is experimental |
| 5 | Task rollback | Use existing `task update --status` — add explicit skill guidance |
| 6 | Checkpoint storage | New `checkpoints` table in `taskops.db`; snapshot = JSON of all task statuses |
| 7 | Project restart | New `project restart` CLI subcommand; `--clear-ops` flag to optionally wipe operation history |
| 8 | Skill placement | TaskBoard → Phase 3 (Execution). Rollback → new Phase 5 after Monitoring |

---

## 3. TaskBoard Integration

### 3.1 Auto-Detection Logic (Skill Instruction)

When entering Phase 3 (Execution), the Agent checks for TaskBoard in this order:
1. `$TASKBOARD_PATH` environment variable
2. `~/TaskBoard` (home directory)
3. `./TaskBoard` (current working directory)

If found → offer to launch. If not found → show install instructions, then continue without it.

### 3.2 Launch Commands

**TUI (stable) — dev mode (no build required):**
```bash
pnpm --filter @taskboard/tui dev -- --path /path/to/project-root
```

**TUI — production (build first):**
```bash
pnpm --filter @taskboard/tui build
node packages/tui/dist/index.js --path /path/to/project-root
```

**Electron (experimental) — dev mode:**
```bash
pnpm rebuild:electron
pnpm --filter @taskboard/electron dev
```

**Electron — production build:**
```bash
pnpm --filter @taskboard/electron build
pnpm --filter @taskboard/electron package
# Installer output: packages/electron/release/
```

**Key controls (TUI):** Tab (switch screen), R (reload), Q (quit), Arrow keys (navigate), Enter (select)

### 3.3 Install Instructions

```bash
git clone https://github.com/godstale/TaskBoard.git
cd TaskBoard
pnpm install
```

> Windows PowerShell users: run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` or use Git Bash/Command Prompt.

### 3.4 Skill Document Changes

- **Phase 3 header**: Add TaskBoard auto-detection block before task execution begins
- **New section "Visualizing with TaskBoard"**: Full manual instructions for TUI and Electron (replaces the existing minimal section)

---

## 4. Rollback & Restart

### 4.1 Task Status Rollback

No new CLI command needed. Use existing `task update`:

```bash
# Rollback a single task to a prior status
python -m cli task update PRJ-T003 --status todo
python -m cli task update PRJ-T003 --status interrupted --interrupt "Reason"

# After rolling back, regenerate TODO.md
python -m cli query generate-todo
```

The skill will add an explicit **Phase 5** section explaining when and how to use this.

### 4.2 Checkpoint-Based Rollback

**New CLI subcommand: `project`**

```bash
# Create a checkpoint (snapshot of all task statuses)
python -m cli project checkpoint --note "After T003 complete"

# List all checkpoints
python -m cli project checkpoint list

# Rollback to a checkpoint (restores all task statuses from snapshot)
python -m cli project rollback --checkpoint 2
```

**DB Schema — new `checkpoints` table:**
```sql
CREATE TABLE checkpoints (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    note        TEXT,
    snapshot    TEXT NOT NULL,   -- JSON: {"PRJ-T001": "done", "PRJ-T002": "todo", ...}
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

**Rollback behavior:**
- Restores `status` and `interrupt` fields for all tasks in snapshot
- Tasks created after the checkpoint are set to `todo`
- Operation history is preserved (not rolled back)
- Regenerates `TODO.md` automatically

### 4.3 Project Restart

```bash
# Reset all tasks to 'todo', preserve operation history
python -m cli project restart

# Reset all tasks to 'todo' AND clear all operation records
python -m cli project restart --clear-ops
```

**Restart behavior:**
- Sets all tasks (except the project root record) to `status='todo'`
- Clears `interrupt`, `seq_order` is preserved
- `--clear-ops`: truncates `operations` table
- Regenerates `TODO.md` automatically
- Creates an automatic checkpoint before restarting (safety net)

---

## 5. Skill Document Structure (After Changes)

```
taskops.md
├── When to Invoke
├── Prerequisites
├── Phase 1: Initialization
├── Phase 2: Planning
├── Phase 3: Execution
│   ├── [NEW] TaskBoard Auto-Detection & Launch
│   ├── Start a Task
│   ├── Record Progress
│   ├── Complete a Task
│   ├── Handle Interruptions
│   └── Handle Errors
├── Phase 4: Monitoring
├── [NEW] Phase 5: Rollback & Restart
│   ├── Task Status Rollback
│   ├── Checkpoint Rollback
│   └── Project Restart
├── Reference: All CLI Commands (updated)
└── [UPDATED] Visualizing with TaskBoard
    ├── Install
    ├── TUI (stable) — dev & production
    └── Electron (experimental) — dev & production
```

---

## 6. CLI Command Reference Updates

| Command | Description |
|---------|-------------|
| `project checkpoint --note` | Create a status snapshot |
| `project checkpoint list` | List all checkpoints |
| `project rollback --checkpoint <id>` | Restore task statuses from checkpoint |
| `project restart [--clear-ops]` | Reset all tasks to todo |

New module: `cli/commands/project.py`

---

## 7. Files to Modify

| File | Change |
|------|--------|
| `skills/taskops.md` | Add Phase 5, update Phase 3 TaskBoard block, update Visualizing section, update CLI reference table |
| `skills/taskops-gemini.md` | Same structural changes (Gemini variant) |
| `cli/commands/project.py` | New file — `checkpoint`, `rollback`, `restart` subcommands |
| `cli/taskops.py` | Register `project` command |
| `cli/db/schema.py` | Add `checkpoints` table creation |
