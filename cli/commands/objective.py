"""Objective management command.
Objective 관리 커맨드 (CRUD). Milestone + date-based events.
"""
from datetime import datetime
from .utils import get_db, get_project_id, next_id, get_workflow_prefix
from ..db.connection import close_connection


def register(subparsers):
    parser = subparsers.add_parser('objective', help='Manage objectives')
    sub = parser.add_subparsers(dest='subcommand')

    create = sub.add_parser('create', help='Create a new objective')
    create.add_argument('--title', required=True, help='Objective title')
    create.add_argument('--milestone', help='Milestone target description')
    create.add_argument('--due-date', help='Due date (YYYY-MM-DD)')
    create.add_argument('--workflow', required=True, help='Workflow ID to associate with')
    create.set_defaults(func=handle_create)

    lst = sub.add_parser('list', help='List all objectives')
    lst.add_argument('--workflow', default=None, help='Filter by workflow ID')
    lst.set_defaults(func=handle_list)

    update = sub.add_parser('update', help='Update an objective')
    update.add_argument('id', help='Objective ID')
    update.add_argument('--status', help='New status')
    update.add_argument('--title', help='New title')
    update.add_argument('--milestone', help='New milestone target')
    update.add_argument('--due-date', help='New due date')
    update.set_defaults(func=handle_update)

    delete = sub.add_parser('delete', help='Delete an objective')
    delete.add_argument('id', help='Objective ID')
    delete.set_defaults(func=handle_delete)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle_create(args):
    conn = get_db(args)
    try:
        project_id = get_project_id(conn)
        wf_short = get_workflow_prefix(args.workflow)
        obj_id = next_id(conn, wf_short, 'O')
        now = datetime.now().isoformat(sep=' ', timespec='seconds')

        milestone = getattr(args, 'milestone', None)
        due_date = getattr(args, 'due_date', None)

        workflow_id = args.workflow
        conn.execute(
            "INSERT INTO tasks (id, project_id, type, title, status, parent_id, "
            "milestone_target, due_date, workflow_id, created_at, updated_at) "
            "VALUES (?, ?, 'objective', ?, 'todo', ?, ?, ?, ?, ?, ?)",
            (obj_id, project_id, args.title, project_id,
             milestone, due_date, workflow_id, now, now)
        )
        conn.commit()

        parts = [f"Created objective: {obj_id} - {args.title}"]
        if milestone:
            parts.append(f"  Milestone: {milestone}")
        if due_date:
            parts.append(f"  Due date: {due_date}")
        print('\n'.join(parts))
    finally:
        close_connection(conn)


def handle_list(args):
    conn = get_db(args)
    try:
        query = "SELECT id, title, status, milestone_target, due_date FROM tasks WHERE type='objective'"
        params = []
        workflow_filter = getattr(args, 'workflow', None)
        if workflow_filter:
            query += " AND workflow_id=?"
            params.append(workflow_filter)
        query += " ORDER BY due_date, id"
        rows = conn.execute(query, params).fetchall()
        if not rows:
            print("No objectives found.")
            return
        for row in rows:
            check = 'x' if row['status'] == 'done' else ' '
            info = []
            if row['milestone_target']:
                info.append(f"milestone: {row['milestone_target']}")
            if row['due_date']:
                info.append(f"due: {row['due_date']}")
            extra = f" ({', '.join(info)})" if info else ""
            print(f"[{check}] {row['id']}: {row['title']}{extra} [{row['status']}]")
    finally:
        close_connection(conn)


def handle_update(args):
    conn = get_db(args)
    try:
        row = conn.execute(
            "SELECT id FROM tasks WHERE id=? AND type='objective'", (args.id,)
        ).fetchone()
        if row is None:
            print(f"Objective not found: {args.id}")
            raise SystemExit(1)

        updates = []
        params = []
        if args.status:
            updates.append("status=?")
            params.append(args.status)
        if args.title:
            updates.append("title=?")
            params.append(args.title)
        if args.milestone is not None:
            updates.append("milestone_target=?")
            params.append(args.milestone)
        due_date = getattr(args, 'due_date', None)
        if due_date is not None:
            updates.append("due_date=?")
            params.append(due_date)

        if not updates:
            print("No updates specified.")
            return

        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        updates.append("updated_at=?")
        params.append(now)
        params.append(args.id)

        conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id=?", params)
        conn.commit()
        print(f"Updated objective: {args.id}")
    finally:
        close_connection(conn)


def handle_delete(args):
    conn = get_db(args)
    try:
        result = conn.execute(
            "DELETE FROM tasks WHERE id=? AND type='objective'", (args.id,)
        )
        conn.commit()
        if result.rowcount == 0:
            print(f"Objective not found: {args.id}")
            raise SystemExit(1)
        print(f"Deleted objective: {args.id}")
    finally:
        close_connection(conn)
