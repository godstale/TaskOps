"""Operation logging command.
Operations 기록 커맨드. AI Agent 작업 이력 관리.
"""
from datetime import datetime
from .utils import get_db
from ..db.connection import close_connection


def register(subparsers, parents=None):
    parser = subparsers.add_parser('op', help='Log operations', parents=parents or [])
    sub = parser.add_subparsers(dest='subcommand')

    start = sub.add_parser('start', help='Record task start')
    start.add_argument('task_id', help='Task ID')
    start.add_argument('--platform', default='unknown', help='Agent platform')
    start.add_argument('--workflow', default=None, help='Workflow ID (auto-resolved from task if omitted)')
    start.set_defaults(func=handle_start)

    progress = sub.add_parser('progress', help='Record progress')
    progress.add_argument('task_id', help='Task ID')
    progress.add_argument('--summary', required=True, help='Progress summary')
    progress.add_argument('--details', help='Details (JSON)')
    progress.add_argument('--subagent', action='store_true', help='Sub agent used')
    progress.add_argument('--tool', default=None, help='Tool used (e.g., Edit, Write, Bash)')
    progress.add_argument('--skill', default=None, help='Skill invoked')
    progress.add_argument('--mcp', default=None, help='MCP server used')
    progress.add_argument('--workflow', default=None, help='Workflow ID (auto-resolved from task if omitted)')
    progress.set_defaults(func=handle_progress)

    complete = sub.add_parser('complete', help='Record task completion')
    complete.add_argument('task_id', help='Task ID')
    complete.add_argument('--summary', required=True, help='Completion summary')
    complete.add_argument('--details', help='Details (JSON)')
    complete.add_argument('--tokens-in', type=int, default=None, dest='tokens_in',
                          help='Input tokens consumed')
    complete.add_argument('--tokens-out', type=int, default=None, dest='tokens_out',
                          help='Output tokens consumed')
    complete.add_argument('--retry-count', type=int, default=0, dest='retry_count',
                          help='Number of retries (default 0)')
    complete.add_argument('--duration', type=int, default=None, dest='duration',
                          help='Duration in seconds')
    complete.add_argument('--workflow', default=None, help='Workflow ID (auto-resolved from task if omitted)')
    complete.set_defaults(func=handle_complete)

    error = sub.add_parser('error', help='Record error')
    error.add_argument('task_id', help='Task ID')
    error.add_argument('--summary', required=True, help='Error summary')
    error.add_argument('--workflow', default=None, help='Workflow ID (auto-resolved from task if omitted)')
    error.set_defaults(func=handle_error)

    interrupt = sub.add_parser('interrupt', help='Record interruption')
    interrupt.add_argument('task_id', help='Task ID')
    interrupt.add_argument('--summary', required=True, help='Interrupt reason')
    interrupt.add_argument('--workflow', default=None, help='Workflow ID (auto-resolved from task if omitted)')
    interrupt.set_defaults(func=handle_interrupt)

    log = sub.add_parser('log', help='Show operation log')
    log.add_argument('--task', help='Filter by task ID')
    log.add_argument('--workflow', default=None, help='Filter by workflow ID')
    log.set_defaults(func=handle_log)

    parser.set_defaults(func=lambda args: parser.print_help())


def _validate_task(conn, task_id):
    row = conn.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone()
    if row is None:
        print(f"Task not found: {task_id}")
        raise SystemExit(1)


def _resolve_workflow_id(conn, args):
    """Resolve workflow_id: use --workflow if given, else auto-resolve from task's workflow_id."""
    wf = getattr(args, 'workflow', None)
    if wf:
        return wf
    row = conn.execute(
        "SELECT workflow_id FROM tasks WHERE id=?", (args.task_id,)
    ).fetchone()
    return row['workflow_id'] if row else None


def handle_start(args):
    conn = get_db(args)
    try:
        _validate_task(conn, args.task_id)
        workflow_id = _resolve_workflow_id(conn, args)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO operations (task_id, operation_type, agent_platform, workflow_id, started_at, created_at) "
            "VALUES (?, 'start', ?, ?, ?, ?)",
            (args.task_id, args.platform, workflow_id, now, now)
        )
        conn.commit()
        print(f"Operation started: {args.task_id} (platform: {args.platform})")
    finally:
        close_connection(conn)


def handle_progress(args):
    conn = get_db(args)
    try:
        _validate_task(conn, args.task_id)
        workflow_id = _resolve_workflow_id(conn, args)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO operations (task_id, operation_type, summary, details, "
            "subagent_used, tool_name, skill_name, mcp_name, workflow_id, created_at) "
            "VALUES (?, 'progress', ?, ?, ?, ?, ?, ?, ?, ?)",
            (args.task_id, args.summary, args.details,
             1 if args.subagent else 0,
             args.tool, args.skill, args.mcp, workflow_id, now)
        )
        conn.commit()
        print(f"Progress recorded: {args.task_id} - {args.summary}")
    finally:
        close_connection(conn)


def handle_complete(args):
    conn = get_db(args)
    try:
        _validate_task(conn, args.task_id)
        workflow_id = _resolve_workflow_id(conn, args)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO operations (task_id, operation_type, summary, details, "
            "input_tokens, output_tokens, retry_count, duration_seconds, "
            "workflow_id, completed_at, created_at) "
            "VALUES (?, 'complete', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (args.task_id, args.summary, args.details,
             args.tokens_in, args.tokens_out, args.retry_count, args.duration,
             workflow_id, now, now)
        )
        conn.commit()
        print(f"Operation completed: {args.task_id} - {args.summary}")
    finally:
        close_connection(conn)


def handle_error(args):
    conn = get_db(args)
    try:
        _validate_task(conn, args.task_id)
        workflow_id = _resolve_workflow_id(conn, args)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO operations (task_id, operation_type, summary, workflow_id, created_at) "
            "VALUES (?, 'error', ?, ?, ?)",
            (args.task_id, args.summary, workflow_id, now)
        )
        conn.commit()
        print(f"Error recorded: {args.task_id} - {args.summary}")
    finally:
        close_connection(conn)


def handle_interrupt(args):
    conn = get_db(args)
    try:
        _validate_task(conn, args.task_id)
        workflow_id = _resolve_workflow_id(conn, args)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO operations (task_id, operation_type, summary, workflow_id, created_at) "
            "VALUES (?, 'interrupt', ?, ?, ?)",
            (args.task_id, args.summary, workflow_id, now)
        )
        conn.commit()
        print(f"Interrupt recorded: {args.task_id} - {args.summary}")
    finally:
        close_connection(conn)


def handle_log(args):
    conn = get_db(args)
    try:
        query = "SELECT * FROM operations WHERE 1=1"
        params = []
        if args.task:
            query += " AND task_id=?"
            params.append(args.task)
        workflow_filter = getattr(args, 'workflow', None)
        if workflow_filter:
            query += " AND workflow_id=?"
            params.append(workflow_filter)
        query += " ORDER BY created_at"
        rows = conn.execute(query, params).fetchall()

        if not rows:
            print("No operations found.")
            return

        for row in rows:
            time = row['started_at'] or row['completed_at'] or row['created_at']
            summary = row['summary'] or '-'
            subagent = " [subagent]" if row['subagent_used'] else ""

            extras = []
            if row['tool_name']:
                extras.append(f"tool:{row['tool_name']}")
            if row['skill_name']:
                extras.append(f"skill:{row['skill_name']}")
            if row['mcp_name']:
                extras.append(f"mcp:{row['mcp_name']}")
            if row['retry_count']:
                extras.append(f"retry:{row['retry_count']}")
            if row['input_tokens'] is not None:
                extras.append(f"in:{row['input_tokens']}")
            if row['output_tokens'] is not None:
                extras.append(f"out:{row['output_tokens']}")
            if row['duration_seconds'] is not None:
                extras.append(f"{row['duration_seconds']}s")
            meta_str = f" [{', '.join(extras)}]" if extras else ""

            print(f"  [{row['id']}] {row['task_id']} {row['operation_type']} "
                  f"({time}) {summary}{subagent}{meta_str}")
    finally:
        close_connection(conn)
