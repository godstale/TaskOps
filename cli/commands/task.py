"""Task/SubTask management command.
Task/SubTask 관리 커맨드 (CRUD). Task와 SubTask는 동일 시퀀스 사용.
"""
from datetime import datetime
from .utils import get_db, get_project_id, next_id, get_workflow_prefix
from ..db.connection import close_connection


def register(subparsers, parents=None):
    parser = subparsers.add_parser('task', help='Manage tasks', parents=parents or [])
    sub = parser.add_subparsers(dest='subcommand')

    create = sub.add_parser('create', help='Create a new task or subtask')
    create.add_argument('--parent', required=True, help='Parent ID (Epic or Task)')
    create.add_argument('--title', required=True, help='Task title')
    create.add_argument('--description', default='', help='Task description')
    create.add_argument('--todo', default='', help='Todo checklist (markdown)')
    create.add_argument('--workflow', required=True, help='Workflow ID to associate with')
    create.set_defaults(func=handle_create)

    lst = sub.add_parser('list', help='List tasks')
    lst.add_argument('--epic', help='Filter by epic ID')
    lst.add_argument('--parent', help='Filter by parent ID')
    lst.add_argument('--status', help='Filter by status')
    lst.add_argument('--workflow', default=None, help='Filter by workflow ID')
    lst.set_defaults(func=handle_list)

    show = sub.add_parser('show', help='Show task details')
    show.add_argument('id', help='Task ID')
    show.set_defaults(func=handle_show)

    update = sub.add_parser('update', help='Update a task')
    update.add_argument('id', help='Task ID')
    update.add_argument('--status', help='New status')
    update.add_argument('--title', help='New title')
    update.add_argument('--description', help='New description')
    update.add_argument('--todo', help='New todo checklist')
    update.add_argument('--interrupt', help='Interrupt reason')
    update.set_defaults(func=handle_update)

    delete = sub.add_parser('delete', help='Delete a task')
    delete.add_argument('id', help='Task ID')
    delete.set_defaults(func=handle_delete)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle_create(args):
    conn = get_db(args)
    try:
        project_id = get_project_id(conn)
        wf_short = get_workflow_prefix(args.workflow)

        # Validate parent exists
        parent = conn.execute(
            "SELECT id, type FROM tasks WHERE id=?", (args.parent,)
        ).fetchone()
        if parent is None:
            print(f"Parent not found: {args.parent}")
            raise SystemExit(1)
        if parent['type'] not in ('epic', 'task'):
            print(f"Invalid parent type: {parent['type']}. Parent must be an epic or task.")
            raise SystemExit(1)

        task_id = next_id(conn, wf_short, 'T')
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        workflow_id = args.workflow
        conn.execute(
            "INSERT INTO tasks (id, project_id, type, title, description, status, parent_id, workflow_id, todo, created_at, updated_at) "
            "VALUES (?, ?, 'task', ?, ?, 'todo', ?, ?, ?, ?, ?)",
            (task_id, project_id, args.title, args.description, args.parent, workflow_id, args.todo, now, now)
        )
        conn.commit()

        label = "subtask" if parent['type'] == 'task' else "task"
        print(f"Created {label}: {task_id} - {args.title} (parent: {args.parent})")
    finally:
        close_connection(conn)


def handle_list(args):
    conn = get_db(args)
    try:
        query = "SELECT id, title, status, parent_id FROM tasks WHERE type='task'"
        params = []

        if args.epic:
            query += " AND (parent_id=? OR parent_id IN (SELECT id FROM tasks WHERE parent_id=? AND type='task'))"
            params.extend([args.epic, args.epic])
        if args.parent:
            query += " AND parent_id=?"
            params.append(args.parent)
        if args.status:
            query += " AND status=?"
            params.append(args.status)
        workflow_filter = getattr(args, 'workflow', None)
        if workflow_filter:
            query += " AND workflow_id=?"
            params.append(workflow_filter)

        query += " ORDER BY seq_order, id"
        rows = conn.execute(query, params).fetchall()

        if not rows:
            print("No tasks found.")
            return
        for row in rows:
            check = 'x' if row['status'] == 'done' else ' '
            print(f"[{check}] {row['id']}: {row['title']} ({row['status']}) [parent: {row['parent_id']}]")
    finally:
        close_connection(conn)


def handle_show(args):
    conn = get_db(args)
    try:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id=? AND type='task'", (args.id,)
        ).fetchone()
        if row is None:
            print(f"Task not found: {args.id}")
            raise SystemExit(1)

        # Determine if this is a subtask
        parent = conn.execute("SELECT type FROM tasks WHERE id=?", (row['parent_id'],)).fetchone()
        label = "SubTask" if parent and parent['type'] == 'task' else "Task"

        print(f"{label}: {row['id']}")
        print(f"  Title: {row['title']}")
        print(f"  Status: {row['status']}")
        print(f"  Parent: {row['parent_id']}")
        print(f"  Workflow: {row['workflow_id'] or '(none)'}")
        print(f"  Description: {row['description'] or '(none)'}")
        if row['todo']:
            print(f"  Todo:\n    {row['todo']}")
        if row['interrupt']:
            print(f"  Interrupt: {row['interrupt']}")
        print(f"  Created: {row['created_at']}")
        print(f"  Updated: {row['updated_at']}")

        # Show child subtasks
        children = conn.execute(
            "SELECT id, title, status FROM tasks WHERE parent_id=? AND type='task' ORDER BY seq_order, id",
            (args.id,)
        ).fetchall()
        if children:
            print(f"  SubTasks ({len(children)}):")
            for child in children:
                check = 'x' if child['status'] == 'done' else ' '
                print(f"    [{check}] {child['id']}: {child['title']} ({child['status']})")
    finally:
        close_connection(conn)


def _sync_epic_status(conn, task_id):
    """After a task status change, propagate the aggregate status to the parent epic."""
    task_row = conn.execute(
        "SELECT parent_id FROM tasks WHERE id=?", (task_id,)
    ).fetchone()
    if not task_row or not task_row['parent_id']:
        return
    parent_id = task_row['parent_id']
    parent = conn.execute(
        "SELECT id, type FROM tasks WHERE id=?", (parent_id,)
    ).fetchone()
    if not parent:
        return

    if parent['type'] == 'epic':
        epic_id = parent['id']
    elif parent['type'] == 'task':
        # Subtask scenario: walk up to find the epic
        gp_row = conn.execute(
            "SELECT parent_id FROM tasks WHERE id=?", (parent_id,)
        ).fetchone()
        if not gp_row or not gp_row['parent_id']:
            return
        gp = conn.execute(
            "SELECT id, type FROM tasks WHERE id=? AND type='epic'", (gp_row['parent_id'],)
        ).fetchone()
        if not gp:
            return
        epic_id = gp['id']
    else:
        return

    children = conn.execute(
        "SELECT status FROM tasks WHERE parent_id=? AND type='task'", (epic_id,)
    ).fetchall()

    if not children:
        return

    statuses = [r['status'] for r in children]
    all_finished = all(s in ('done', 'cancelled') for s in statuses)
    any_done = any(s == 'done' for s in statuses)
    any_active = any(s in ('done', 'in_progress') for s in statuses)

    if all_finished and any_done:
        new_status = 'done'
    elif any_active:
        new_status = 'in_progress'
    else:
        new_status = 'todo'

    now = datetime.now().isoformat(sep=' ', timespec='seconds')
    conn.execute(
        "UPDATE tasks SET status=?, updated_at=? WHERE id=? AND type='epic'",
        (new_status, now, epic_id)
    )


def handle_update(args):
    conn = get_db(args)
    try:
        row = conn.execute("SELECT id FROM tasks WHERE id=? AND type='task'", (args.id,)).fetchone()
        if row is None:
            print(f"Task not found: {args.id}")
            raise SystemExit(1)

        updates = []
        params = []
        if args.status:
            updates.append("status=?")
            params.append(args.status)
        if args.title:
            updates.append("title=?")
            params.append(args.title)
        if args.description is not None:
            updates.append("description=?")
            params.append(args.description)
        if args.todo is not None:
            updates.append("todo=?")
            params.append(args.todo)
        if args.interrupt is not None:
            updates.append("interrupt=?")
            params.append(args.interrupt)

        if not updates:
            print("No updates specified.")
            return

        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        updates.append("updated_at=?")
        params.append(now)
        params.append(args.id)

        conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id=?", params)

        # Auto-sync parent epic status when task status changes
        if args.status:
            _sync_epic_status(conn, args.id)

        conn.commit()
        print(f"Updated task: {args.id}")
    finally:
        close_connection(conn)


def handle_delete(args):
    conn = get_db(args)
    try:
        children = conn.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE parent_id=?", (args.id,)
        ).fetchone()
        if children['cnt'] > 0:
            print(f"Warning: Task {args.id} has {children['cnt']} subtask(s). Delete them first.")
            raise SystemExit(1)

        result = conn.execute("DELETE FROM tasks WHERE id=? AND type='task'", (args.id,))
        conn.commit()
        if result.rowcount == 0:
            print(f"Task not found: {args.id}")
            raise SystemExit(1)
        print(f"Deleted task: {args.id}")
    finally:
        close_connection(conn)
