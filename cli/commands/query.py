"""Status query and report generation command.
상태 조회 및 리포트 생성 커맨드.
"""
import json
from datetime import datetime
from .utils import get_db, get_project_dir
from ..db.connection import close_connection


def register(subparsers):
    parser = subparsers.add_parser('query', help='Query status and generate reports')
    sub = parser.add_subparsers(dest='subcommand')

    status = sub.add_parser('status', help='Show project status summary')
    status.set_defaults(func=handle_status)

    tasks = sub.add_parser('tasks', help='List tasks by filter')
    tasks.add_argument('--status', help='Filter by status')
    tasks.set_defaults(func=handle_tasks)

    show = sub.add_parser('show', help='Print task structure to stdout')
    show.add_argument('--workflow', help='Filter output to a specific workflow ID')
    show.set_defaults(func=handle_show)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle_status(args):
    conn = get_db(args)
    try:
        project = conn.execute(
            "SELECT id, title FROM tasks WHERE type='project' LIMIT 1"
        ).fetchone()
        if not project:
            print("No project found.")
            return

        # Count by type
        epic_count = conn.execute(
            "SELECT COUNT(*) as c FROM tasks WHERE type='epic'"
        ).fetchone()['c']
        task_count = conn.execute(
            "SELECT COUNT(*) as c FROM tasks WHERE type='task'"
        ).fetchone()['c']
        obj_count = conn.execute(
            "SELECT COUNT(*) as c FROM tasks WHERE type='objective'"
        ).fetchone()['c']

        # Count by status (tasks only)
        statuses = conn.execute(
            "SELECT status, COUNT(*) as c FROM tasks WHERE type='task' GROUP BY status"
        ).fetchall()
        status_map = {row['status']: row['c'] for row in statuses}

        done = status_map.get('done', 0)
        total = task_count
        pct = (done / total * 100) if total > 0 else 0

        print(f"Project: {project['title']} ({project['id']})")
        print(f"  Epics: {epic_count}")
        print(f"  Tasks: {task_count}")
        print(f"  Objectives: {obj_count}")
        print(f"  Progress: {done}/{total} ({pct:.0f}%)")
        if status_map:
            print("  Status breakdown:")
            for s in ['todo', 'in_progress', 'interrupted', 'done', 'cancelled']:
                if s in status_map:
                    print(f"    {s}: {status_map[s]}")
    finally:
        close_connection(conn)


def handle_tasks(args):
    conn = get_db(args)
    try:
        query = "SELECT id, title, status, parent_id FROM tasks WHERE type='task'"
        params = []
        if args.status:
            query += " AND status=?"
            params.append(args.status)
        query += " ORDER BY seq_order, id"

        rows = conn.execute(query, params).fetchall()
        if not rows:
            print("No tasks found.")
            return
        for row in rows:
            check = 'x' if row['status'] == 'done' else ' '
            print(f"[{check}] {row['id']}: {row['title']} ({row['status']})")
    finally:
        close_connection(conn)


def handle_show(args):
    conn = get_db(args)
    try:
        project = conn.execute(
            "SELECT id, title FROM tasks WHERE type='project' LIMIT 1"
        ).fetchone()
        if not project:
            print("No project found.")
            return

        workflow_filter = getattr(args, 'workflow', None)

        if workflow_filter:
            workflows = conn.execute(
                "SELECT id, title FROM workflows WHERE id=? ORDER BY id",
                (workflow_filter,)
            ).fetchall()
        else:
            workflows = conn.execute(
                "SELECT id, title FROM workflows ORDER BY id"
            ).fetchall()

        # Tasks not belonging to any workflow (legacy / no workflow_id)
        if not workflow_filter:
            _print_section(conn, None)

        for wf in workflows:
            print(f"\n{'═' * 3} {wf['id']}: {wf['title']} {'═' * 3}")
            _print_section(conn, wf['id'])

        # Objectives (shown once, not scoped to workflow)
        objectives = conn.execute(
            "SELECT id, title, status, milestone_target, due_date "
            "FROM tasks WHERE type='objective' ORDER BY due_date, id"
        ).fetchall()
        if objectives:
            print("\n[Objectives]")
            for obj in objectives:
                check = '●' if obj['status'] == 'done' else '○'
                info = f" — {obj['milestone_target']}" if obj['milestone_target'] else ""
                if obj['due_date']:
                    info = f" — {obj['due_date']}"
                print(f"  {check} {obj['id']}: {obj['title']}{info}")
    finally:
        close_connection(conn)


def _print_section(conn, workflow_id):
    """Print workflow order + ETS detail for a given workflow_id (None = no workflow)."""
    if workflow_id is not None:
        wf_sql = "AND workflow_id=?"
        wf_params = [workflow_id]
    else:
        wf_sql = "AND (workflow_id IS NULL)"
        wf_params = []

    # Workflow order
    ordered = conn.execute(
        f"SELECT id, title, parallel_group FROM tasks "
        f"WHERE type='task' AND seq_order IS NOT NULL {wf_sql} "
        f"ORDER BY seq_order, id",
        wf_params
    ).fetchall()

    if ordered:
        print("\n[Workflow Order]")
        seen_groups = {}
        order_num = 0
        for wt in ordered:
            group = wt['parallel_group']
            if group and group in seen_groups:
                print(f"   - {wt['id']}: {wt['title']}")
            elif group:
                order_num += 1
                seen_groups[group] = order_num
                print(f"{order_num}. [parallel-group: {group}]")
                print(f"   - {wt['id']}: {wt['title']}")
            else:
                order_num += 1
                print(f"{order_num}. {wt['id']}: {wt['title']}")

    # ETS detail by epic
    epics = conn.execute(
        f"SELECT id, title, status FROM tasks WHERE type='epic' {wf_sql} ORDER BY id",
        wf_params
    ).fetchall()

    if epics:
        print("\n[ETS Detail]")
        for epic in epics:
            print(f"Epic {epic['id']}: {epic['title']} [{epic['status']}]")
            _print_task_tree(conn, epic['id'], indent=2)


def _print_task_tree(conn, parent_id, indent):
    """Recursively print task tree."""
    tasks = conn.execute(
        "SELECT id, title, status FROM tasks "
        "WHERE type='task' AND parent_id=? ORDER BY seq_order, id",
        (parent_id,)
    ).fetchall()
    prefix = ' ' * indent
    for task in tasks:
        check = '●' if task['status'] == 'done' else '○'
        print(f"{prefix}{check} {task['id']}: {task['title']} [{task['status']}]")
        _print_task_tree(conn, task['id'], indent + 2)
