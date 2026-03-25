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
    rs = sub.add_parser('restart', help='Reset all tasks to todo and clear operation history')
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

    # Always clear operations on restart (clean slate for re-execution)
    conn.execute("DELETE FROM operations")
    print("  Operation history cleared.")

    conn.commit()
    close_connection(conn)
    tasks_reset = len(snapshot)
    print(f"Project restarted: {tasks_reset} tasks reset to 'todo'")
    print("  Auto-checkpoint saved before restart.")
