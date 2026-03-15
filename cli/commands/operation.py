"""Operation logging command.
Operations 기록 커맨드. AI Agent 작업 이력 관리.
"""
from datetime import datetime
from .utils import get_db
from ..db.connection import close_connection


def register(subparsers):
    parser = subparsers.add_parser('op', help='Log operations')
    sub = parser.add_subparsers(dest='subcommand')

    start = sub.add_parser('start', help='Record task start')
    start.add_argument('task_id', help='Task ID')
    start.add_argument('--platform', default='unknown', help='Agent platform')
    start.set_defaults(func=handle_start)

    progress = sub.add_parser('progress', help='Record progress')
    progress.add_argument('task_id', help='Task ID')
    progress.add_argument('--summary', required=True, help='Progress summary')
    progress.add_argument('--details', help='Details (JSON)')
    progress.add_argument('--subagent', action='store_true', help='Sub agent used')
    progress.set_defaults(func=handle_progress)

    complete = sub.add_parser('complete', help='Record task completion')
    complete.add_argument('task_id', help='Task ID')
    complete.add_argument('--summary', required=True, help='Completion summary')
    complete.add_argument('--details', help='Details (JSON)')
    complete.set_defaults(func=handle_complete)

    error = sub.add_parser('error', help='Record error')
    error.add_argument('task_id', help='Task ID')
    error.add_argument('--summary', required=True, help='Error summary')
    error.set_defaults(func=handle_error)

    interrupt = sub.add_parser('interrupt', help='Record interruption')
    interrupt.add_argument('task_id', help='Task ID')
    interrupt.add_argument('--summary', required=True, help='Interrupt reason')
    interrupt.set_defaults(func=handle_interrupt)

    log = sub.add_parser('log', help='Show operation log')
    log.add_argument('--task', help='Filter by task ID')
    log.set_defaults(func=handle_log)

    parser.set_defaults(func=lambda args: parser.print_help())


def _validate_task(conn, task_id):
    row = conn.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone()
    if row is None:
        print(f"Task not found: {task_id}")
        raise SystemExit(1)


def handle_start(args):
    conn = get_db(args)
    try:
        _validate_task(conn, args.task_id)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO operations (task_id, operation_type, agent_platform, started_at, created_at) "
            "VALUES (?, 'start', ?, ?, ?)",
            (args.task_id, args.platform, now, now)
        )
        conn.commit()
        print(f"Operation started: {args.task_id} (platform: {args.platform})")
    finally:
        close_connection(conn)


def handle_progress(args):
    conn = get_db(args)
    try:
        _validate_task(conn, args.task_id)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO operations (task_id, operation_type, summary, details, "
            "subagent_used, created_at) VALUES (?, 'progress', ?, ?, ?, ?)",
            (args.task_id, args.summary, args.details,
             1 if args.subagent else 0, now)
        )
        conn.commit()
        print(f"Progress recorded: {args.task_id} - {args.summary}")
    finally:
        close_connection(conn)


def handle_complete(args):
    conn = get_db(args)
    try:
        _validate_task(conn, args.task_id)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO operations (task_id, operation_type, summary, details, "
            "completed_at, created_at) VALUES (?, 'complete', ?, ?, ?, ?)",
            (args.task_id, args.summary, args.details, now, now)
        )
        conn.commit()
        print(f"Operation completed: {args.task_id} - {args.summary}")
    finally:
        close_connection(conn)


def handle_error(args):
    conn = get_db(args)
    try:
        _validate_task(conn, args.task_id)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO operations (task_id, operation_type, summary, created_at) "
            "VALUES (?, 'error', ?, ?)",
            (args.task_id, args.summary, now)
        )
        conn.commit()
        print(f"Error recorded: {args.task_id} - {args.summary}")
    finally:
        close_connection(conn)


def handle_interrupt(args):
    conn = get_db(args)
    try:
        _validate_task(conn, args.task_id)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO operations (task_id, operation_type, summary, created_at) "
            "VALUES (?, 'interrupt', ?, ?)",
            (args.task_id, args.summary, now)
        )
        conn.commit()
        print(f"Interrupt recorded: {args.task_id} - {args.summary}")
    finally:
        close_connection(conn)


def handle_log(args):
    conn = get_db(args)
    try:
        if args.task:
            rows = conn.execute(
                "SELECT * FROM operations WHERE task_id=? ORDER BY created_at",
                (args.task,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM operations ORDER BY created_at"
            ).fetchall()

        if not rows:
            print("No operations found.")
            return

        for row in rows:
            time = row['started_at'] or row['completed_at'] or row['created_at']
            summary = row['summary'] or '-'
            subagent = " [subagent]" if row['subagent_used'] else ""
            print(f"  [{row['id']}] {row['task_id']} {row['operation_type']} "
                  f"({time}) {summary}{subagent}")
    finally:
        close_connection(conn)
