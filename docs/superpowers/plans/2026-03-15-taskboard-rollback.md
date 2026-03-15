# TaskBoard Integration & Rollback Support — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add TaskBoard auto-detection/installation guidance, full TUI+Electron usage docs, and three rollback mechanisms (task status, checkpoint, project restart) to the TaskOps skill and CLI.

**Architecture:** Two parallel tracks — (1) Python CLI backend adds a new `project` command with `checkpoint`, `rollback`, and `restart` subcommands plus a new `checkpoints` DB table; (2) Both skill documents (`taskops.md`, `taskops-gemini.md`) are updated with TaskBoard auto-detection logic, complete manual usage instructions, and a new Phase 5 Rollback section.

**Tech Stack:** Python 3.10+, SQLite (`sqlite3`), argparse, Markdown skill documents

---

## Chunk 1: CLI Backend — DB Schema + project command

### Task 1: Add `checkpoints` table to DB schema

**Files:**
- Modify: `cli/db/schema.py`

`create_tables()` already uses `CREATE TABLE IF NOT EXISTS` for all tables, so it is idempotent and handles existing DBs automatically. No migration function is needed — just add the new table to `create_tables()`.

- [ ] **Step 1: Add SQL_CREATE_CHECKPOINTS constant**

  In `cli/db/schema.py`, add after `SQL_CREATE_SETTINGS`:

  ```python
  SQL_CREATE_CHECKPOINTS = """
  CREATE TABLE IF NOT EXISTS checkpoints (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      note        TEXT,
      snapshot    TEXT NOT NULL,
      created_at  TEXT NOT NULL DEFAULT (datetime('now'))
  );
  """
  ```

- [ ] **Step 2: Call it in create_tables()**

  In the `create_tables(conn)` function, add after `conn.execute(SQL_CREATE_SETTINGS)`:

  ```python
  conn.execute(SQL_CREATE_CHECKPOINTS)
  ```

  The complete `create_tables` body should now be:
  ```python
  def create_tables(conn):
      conn.execute(SQL_CREATE_TASKS)
      conn.execute(SQL_CREATE_OPERATIONS)
      conn.execute(SQL_CREATE_RESOURCES)
      conn.execute(SQL_CREATE_SETTINGS)
      conn.execute(SQL_CREATE_CHECKPOINTS)
      for idx_sql in SQL_CREATE_INDEXES:
          conn.execute(idx_sql)
      conn.commit()
  ```

- [ ] **Step 3: Verify schema creation**

  ```bash
  python -c "
  import sqlite3, sys
  sys.path.insert(0, '.')
  from cli.db.schema import create_tables
  conn = sqlite3.connect('/tmp/test_schema.db')
  create_tables(conn)
  cols = [r[1] for r in conn.execute(\"PRAGMA table_info(checkpoints)\")]
  assert cols == ['id', 'note', 'snapshot', 'created_at'], f'Got: {cols}'
  print('checkpoints table OK')
  "
  ```
  Expected: `checkpoints table OK`

- [ ] **Step 4: Commit**

  ```bash
  git add cli/db/schema.py
  git commit -m "feat: add checkpoints table to DB schema"
  ```

---

### Task 2: Implement `cli/commands/project.py`

**Files:**
- Create: `cli/commands/project.py`

This module handles three subcommands: `checkpoint` (with optional `list` action), `rollback`, and `restart`.

The `checkpoint` subcommand uses an optional positional `action` argument so that:
- `project checkpoint --note "..."` → creates a checkpoint
- `project checkpoint list` → lists all checkpoints

- [ ] **Step 1: Create the file with register() and checkpoint handler**

  ```python
  """Project-level management commands: checkpoint, rollback, restart.
  프로젝트 레벨 관리 커맨드: 체크포인트, 롤백, 재시작.
  """
  import json
  from datetime import datetime
  from .utils import get_db, get_project_id
  from ..db.connection import close_connection


  def register(subparsers):
      parser = subparsers.add_parser('project', help='Project-level management')
      sub = parser.add_subparsers(dest='subcommand')

      # checkpoint — create or list
      cp = sub.add_parser('checkpoint', help='Create a snapshot or list snapshots')
      cp.add_argument('action', nargs='?', choices=['list'], default=None,
                      help='list: show all checkpoints (omit to create)')
      cp.add_argument('--note', default='', help='Checkpoint description (for create)')
      cp.set_defaults(func=handle_checkpoint)

      # rollback
      rb = sub.add_parser('rollback', help='Restore task statuses from a checkpoint')
      rb.add_argument('--checkpoint', required=True, type=int, help='Checkpoint ID')
      rb.set_defaults(func=handle_rollback)

      # restart
      rs = sub.add_parser('restart', help='Reset all tasks to todo')
      rs.add_argument('--clear-ops', action='store_true',
                      help='Also clear all operation records')
      rs.set_defaults(func=handle_restart)


  def _snapshot_tasks(conn, project_id):
      """Capture current status of all non-project tasks as a dict.
      프로젝트 루트를 제외한 모든 Task의 현재 상태를 딕셔너리로 캡처.
      """
      rows = conn.execute(
          "SELECT id, status, interrupt FROM tasks "
          "WHERE project_id = ? AND type != 'project'",
          (project_id,)
      ).fetchall()
      return {row[0]: {'status': row[1], 'interrupt': row[2]} for row in rows}


  def handle_checkpoint(args):
      if args.action == 'list':
          _list_checkpoints(args)
      else:
          _create_checkpoint(args)


  def _create_checkpoint(args):
      conn = get_db(args)
      project_id = get_project_id(conn)
      snapshot = _snapshot_tasks(conn, project_id)
      conn.execute(
          "INSERT INTO checkpoints (note, snapshot) VALUES (?, ?)",
          (args.note, json.dumps(snapshot))
      )
      conn.commit()
      cp_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
      close_connection(conn)
      print(f"Checkpoint #{cp_id} created: {args.note or '(no note)'}")
      print(f"  Snapshot: {len(snapshot)} tasks captured")


  def _list_checkpoints(args):
      conn = get_db(args)
      rows = conn.execute(
          "SELECT id, note, created_at, snapshot FROM checkpoints ORDER BY id"
      ).fetchall()
      close_connection(conn)
      if not rows:
          print("No checkpoints found.")
          return
      print(f"{'ID':<4} {'Created':<20} {'Tasks':<6} Note")
      print("-" * 60)
      for row in rows:
          snap = json.loads(row['snapshot'])
          note = row['note'] or '(no note)'
          print(f"{row['id']:<4} {row['created_at']:<20} {len(snap):<6} {note}")


  def handle_rollback(args):
      conn = get_db(args)
      row = conn.execute(
          "SELECT id, note, snapshot FROM checkpoints WHERE id = ?",
          (args.checkpoint,)
      ).fetchone()
      if not row:
          close_connection(conn)
          print(f"Error: checkpoint #{args.checkpoint} not found.")
          return

      snapshot = json.loads(row['snapshot'])
      note = row['note'] or '(no note)'

      # Auto-save current state as safety checkpoint before rollback
      project_id = get_project_id(conn)
      current = _snapshot_tasks(conn, project_id)
      conn.execute(
          "INSERT INTO checkpoints (note, snapshot) VALUES (?, ?)",
          (f"[auto] before rollback to #{args.checkpoint}", json.dumps(current))
      )

      # Restore statuses from snapshot
      restored = 0
      for task_id, state in snapshot.items():
          conn.execute(
              "UPDATE tasks SET status = ?, interrupt = ?, updated_at = ? WHERE id = ?",
              (state['status'], state['interrupt'], datetime.now().isoformat(), task_id)
          )
          restored += 1

      # Tasks created after checkpoint → reset to todo
      snap_ids = set(snapshot.keys())
      all_rows = conn.execute(
          "SELECT id FROM tasks WHERE project_id = ? AND type != 'project'",
          (project_id,)
      ).fetchall()
      for r in all_rows:
          if r['id'] not in snap_ids:
              conn.execute(
                  "UPDATE tasks SET status = 'todo', interrupt = NULL, updated_at = ? "
                  "WHERE id = ?",
                  (datetime.now().isoformat(), r['id'])
              )

      conn.commit()
      close_connection(conn)
      print(f"Rolled back to checkpoint #{args.checkpoint}: {note}")
      print(f"  Restored: {restored} tasks")
      print("  Regenerate TODO.md: python -m cli query generate-todo")


  def handle_restart(args):
      conn = get_db(args)
      project_id = get_project_id(conn)

      # Auto-save checkpoint before restart
      snapshot = _snapshot_tasks(conn, project_id)
      conn.execute(
          "INSERT INTO checkpoints (note, snapshot) VALUES (?, ?)",
          ('[auto] before restart', json.dumps(snapshot))
      )

      # Reset all non-project tasks to todo
      conn.execute(
          "UPDATE tasks SET status = 'todo', interrupt = NULL, updated_at = ? "
          "WHERE project_id = ? AND type != 'project'",
          (datetime.now().isoformat(), project_id)
      )

      if args.clear_ops:
          conn.execute("DELETE FROM operations")
          print("  Operation history cleared.")

      conn.commit()
      close_connection(conn)
      tasks_reset = len(snapshot)
      print(f"Project restarted: {tasks_reset} tasks reset to 'todo'")
      print("  Auto-checkpoint saved before restart.")
      print("  Regenerate TODO.md: python -m cli query generate-todo")
  ```

- [ ] **Step 2: Verify manually**

  ```bash
  python -m cli init --name Test --prefix TST --path /tmp/taskops_test
  python -m cli --db /tmp/taskops_test/taskops.db epic create --title "Epic 1"
  python -m cli --db /tmp/taskops_test/taskops.db task create --parent TST-E001 --title "Task 1"
  python -m cli --db /tmp/taskops_test/taskops.db project checkpoint --note "initial"
  python -m cli --db /tmp/taskops_test/taskops.db task update TST-T001 --status done
  python -m cli --db /tmp/taskops_test/taskops.db project checkpoint list
  ```
  Expected: table showing checkpoint #1 with note "initial"

  ```bash
  python -m cli --db /tmp/taskops_test/taskops.db project rollback --checkpoint 1
  python -m cli --db /tmp/taskops_test/taskops.db task show TST-T001
  ```
  Expected: TST-T001 status = `todo`

  ```bash
  python -m cli --db /tmp/taskops_test/taskops.db task update TST-T001 --status in_progress
  python -m cli --db /tmp/taskops_test/taskops.db project restart
  python -m cli --db /tmp/taskops_test/taskops.db task show TST-T001
  ```
  Expected: TST-T001 status = `todo`

  ```bash
  python -m cli --db /tmp/taskops_test/taskops.db project restart --clear-ops
  python -m cli --db /tmp/taskops_test/taskops.db op log
  ```
  Expected: empty log

- [ ] **Step 3: Commit**

  ```bash
  git add cli/commands/project.py
  git commit -m "feat: add project checkpoint, rollback, and restart commands"
  ```

---

### Task 3: Register `project` command in taskops.py

**Files:**
- Modify: `cli/taskops.py`

- [ ] **Step 1: Add import and register call**

  In `cli/taskops.py`, add to the imports block (after the existing imports):
  ```python
  from .commands.project import register as register_project
  ```

  Add to the register calls (after `register_setting(subparsers)`):
  ```python
  register_project(subparsers)
  ```

- [ ] **Step 2: Update version to 0.3.0**

  ```python
  __version__ = "0.3.0"
  ```

- [ ] **Step 3: Verify help output**

  ```bash
  python -m cli --help
  ```
  Expected: `project` appears in the commands list.

  ```bash
  python -m cli project --help
  ```
  Expected: shows `checkpoint`, `rollback`, `restart` subcommands.

  ```bash
  python -m cli project checkpoint --help
  ```
  Expected: shows optional `action` positional (choices: `list`) and `--note` flag.

- [ ] **Step 4: Commit**

  ```bash
  git add cli/taskops.py
  git commit -m "feat: register project command in CLI entry point, bump version to 0.3.0"
  ```

---

## Chunk 2: Skill Document Updates

### Task 4: Update `skills/taskops.md`

**Files:**
- Modify: `skills/taskops.md`

Four changes in this file:

#### Change A — Phase 3 TaskBoard auto-detection block

- [ ] **Step 1: Replace the current Phase 3 TaskBoard block**

  Find and replace this block (the paragraph starting with "Before starting work, **guide the user to launch TaskBoard**..." through the closing blockquote):

  ```markdown
  Before starting work, **guide the user to launch TaskBoard** for real-time monitoring:

  ```bash
  # In a separate terminal — run from the TaskBoard directory
  pnpm --filter @taskboard/tui dev -- --path /path/to/project-root
  ```

  > TaskBoard watches `taskops.db` and refreshes automatically as tasks progress.
  > If TaskBoard is not installed, see the [Visualizing with TaskBoard](#visualizing-with-taskboard) section.
  ```

  Replace with:

  ```markdown
  ### Launch TaskBoard (Optional — Real-time Monitoring)

  Before starting work, check if TaskBoard is available and offer to launch it.

  **Step 1 — Detect installation** (check in order):
  1. `$TASKBOARD_PATH` environment variable
  2. `~/TaskBoard`
  3. `./TaskBoard` (relative to cwd)

  **Step 2 — If found**, launch TUI in a separate terminal (from the TaskBoard directory):
  ```bash
  pnpm --filter @taskboard/tui dev -- --path /path/to/project-root
  ```

  **Step 3 — If not found**, notify the user and continue without it:
  > TaskBoard is not installed. Work will proceed normally.
  > See [Visualizing with TaskBoard](#visualizing-with-taskboard) for install steps.

  > TaskBoard watches `taskops.db` and refreshes automatically as tasks progress.
  ```

#### Change B — Add Phase 5: Rollback & Restart

- [ ] **Step 2: Insert Phase 5 before `## Reference: All CLI Commands`**

  ````markdown
  ---

  ## Phase 5: Rollback & Restart

  Use when a task needs to be retried, the project needs to return to a known-good state, or execution must restart from scratch.

  ### Task Status Rollback

  Roll back a single task to a previous status using the existing `task update` command:

  ```bash
  # Set a completed task back to todo (re-run it)
  python -m cli task update PRJ-T003 --status todo

  # Set a task to interrupted with a reason
  python -m cli task update PRJ-T003 --status interrupted --interrupt "Needs redesign"

  # Regenerate TODO.md after any status change
  python -m cli query generate-todo
  ```

  ### Checkpoint Rollback

  Capture the current state as a snapshot and roll back to any previous snapshot:

  ```bash
  # Create a checkpoint at any meaningful point during execution
  python -m cli project checkpoint --note "After T003 complete"

  # List all checkpoints
  python -m cli project checkpoint list

  # Roll back all task statuses to a checkpoint
  # (auto-saves current state as a safety checkpoint first)
  python -m cli project rollback --checkpoint 2

  # Regenerate TODO.md after rollback
  python -m cli query generate-todo
  ```

  > Checkpoint snapshots preserve `status` and `interrupt` fields for all tasks.
  > Operation history is NOT rolled back — the log is always preserved.
  > Tasks created after the checkpoint are reset to `todo` on rollback.

  ### Project Restart

  Reset all tasks to `todo` and start over:

  ```bash
  # Reset all tasks to todo (operation history preserved)
  python -m cli project restart

  # Reset all tasks to todo AND clear operation history
  python -m cli project restart --clear-ops

  # Regenerate TODO.md after restart
  python -m cli query generate-todo
  ```

  > `project restart` automatically creates a checkpoint before resetting, so you can roll back if needed.
  ````

#### Change C — Update CLI Reference Table

- [ ] **Step 3: Add project commands to the Reference table**

  In `## Reference: All CLI Commands`, add these rows after the `setting` row:

  ```markdown
  | `project checkpoint [--note]` | Create a status snapshot |
  | `project checkpoint list` | List all checkpoints |
  | `project rollback --checkpoint <id>` | Restore task statuses from checkpoint |
  | `project restart [--clear-ops]` | Reset all tasks to todo |
  ```

#### Change D — Update Visualizing with TaskBoard section

- [ ] **Step 4: Replace the existing `## Visualizing with TaskBoard` section**

  ````markdown
  ## Visualizing with TaskBoard

  TaskBoard is a standalone read-only GUI that visualizes the TaskOps database in real-time.
  Two interface modes are available: TUI (terminal, stable) and Electron (desktop, experimental).

  ### Install

  ```bash
  git clone https://github.com/godstale/TaskBoard.git
  cd TaskBoard
  pnpm install
  ```

  > **Windows PowerShell users:** run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
  > or use Git Bash / Command Prompt instead.

  ### TUI Mode (Stable)

  **Quick start — dev mode (no build required):**
  ```bash
  # Run from the TaskBoard directory
  pnpm --filter @taskboard/tui dev -- --path /path/to/project-root
  ```

  **Production — build first, then run:**
  ```bash
  pnpm --filter @taskboard/tui build
  node packages/tui/dist/index.js --path /path/to/project-root
  ```

  **Key controls:** `Tab` switch screen · `R` reload · `Q` quit · `↑↓` navigate · `Enter` select

  ### Electron Mode (Experimental)

  **Dev mode:**
  ```bash
  # First-time setup — rebuild native modules for your Node version
  pnpm rebuild:electron

  # Launch
  pnpm --filter @taskboard/electron dev
  ```

  **Production build:**
  ```bash
  pnpm --filter @taskboard/electron build
  pnpm --filter @taskboard/electron package
  # Installers output to: packages/electron/release/
  ```

  > `--path` points to the project root directory (the folder containing `taskops.db`).
  > TaskBoard watches `taskops.db` and automatically refreshes when the DB changes.

  → [TaskBoard GitHub](https://github.com/godstale/TaskBoard)
  ````

- [ ] **Step 5: Verify the file has all required sections**

  ```bash
  python -c "
  with open('skills/taskops.md') as f:
      content = f.read()
  checks = [
      'Phase 5',
      'project checkpoint list',
      'project restart',
      'TUI Mode (Stable)',
      'Electron Mode (Experimental)',
      'pnpm rebuild:electron',
      'Detect installation',
  ]
  for c in checks:
      assert c in content, f'MISSING: {c}'
  print('taskops.md OK')
  "
  ```
  Expected: `taskops.md OK`

- [ ] **Step 6: Commit**

  ```bash
  git add skills/taskops.md
  git commit -m "docs: update taskops.md — TaskBoard auto-detection, Phase 5 rollback, full TaskBoard usage guide"
  ```

---

### Task 5: Update `skills/taskops-gemini.md`

**Files:**
- Modify: `skills/taskops-gemini.md`

Apply the same four changes as Task 4. The rollback commands are identical (CLI-based, no hooks involved).

- [ ] **Step 1: Replace Phase 3 TaskBoard block** (identical to Task 4 Change A)

- [ ] **Step 2: Add Phase 5: Rollback & Restart** (identical to Task 4 Change B)

  Insert before `## Gemini CLI Tool Mapping`.

- [ ] **Step 3: Update CLI Reference Table** (identical rows as Task 4 Change C)

- [ ] **Step 4: Replace Visualizing with TaskBoard section** (identical to Task 4 Change D)

- [ ] **Step 5: Verify the file has all required sections**

  ```bash
  python -c "
  with open('skills/taskops-gemini.md') as f:
      content = f.read()
  checks = [
      'Phase 5',
      'project checkpoint list',
      'project restart',
      'TUI Mode (Stable)',
      'Electron Mode (Experimental)',
      'pnpm rebuild:electron',
      'Detect installation',
  ]
  for c in checks:
      assert c in content, f'MISSING: {c}'
  print('taskops-gemini.md OK')
  "
  ```
  Expected: `taskops-gemini.md OK`

- [ ] **Step 6: Commit**

  ```bash
  git add skills/taskops-gemini.md
  git commit -m "docs: update taskops-gemini.md — TaskBoard auto-detection, Phase 5 rollback, full TaskBoard usage guide"
  ```

---

## Final Verification

- [ ] **Run full CLI smoke test**

  ```bash
  python -m cli --help
  python -m cli project --help
  python -m cli project checkpoint --help
  python -m cli project rollback --help
  python -m cli project restart --help
  ```
  Expected: all commands show help without errors.

- [ ] **Confirm skill files have all required sections**

  ```bash
  python -c "
  for fname in ['skills/taskops.md', 'skills/taskops-gemini.md']:
      content = open(fname).read()
      checks = [
          'Phase 5',
          'project checkpoint list',
          'project restart',
          'TUI Mode (Stable)',
          'Electron Mode (Experimental)',
          'pnpm rebuild:electron',
          'Detect installation',
      ]
      for c in checks:
          assert c in content, f'MISSING in {fname}: {c}'
      print(f'{fname}: all checks passed')
  "
  ```
