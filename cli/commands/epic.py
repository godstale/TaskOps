"""Epic management command.
Epic 관리 커맨드 (CRUD).
"""
from datetime import datetime
from .utils import get_db, get_project_id, next_id
from ..db.connection import close_connection


def register(subparsers):
    parser = subparsers.add_parser('epic', help='Manage epics')
    sub = parser.add_subparsers(dest='subcommand')

    create = sub.add_parser('create', help='Create a new epic')
    create.add_argument('--title', required=True, help='Epic title')
    create.add_argument('--description', default='', help='Epic description')
    create.set_defaults(func=handle_create)

    lst = sub.add_parser('list', help='List all epics')
    lst.set_defaults(func=handle_list)

    show = sub.add_parser('show', help='Show epic details')
    show.add_argument('id', help='Epic ID')
    show.set_defaults(func=handle_show)

    update = sub.add_parser('update', help='Update an epic')
    update.add_argument('id', help='Epic ID')
    update.add_argument('--status', help='New status')
    update.add_argument('--title', help='New title')
    update.add_argument('--description', help='New description')
    update.set_defaults(func=handle_update)

    delete = sub.add_parser('delete', help='Delete an epic')
    delete.add_argument('id', help='Epic ID')
    delete.set_defaults(func=handle_delete)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle_create(args):
    conn = get_db(args)
    try:
        project_id = get_project_id(conn)
        epic_id = next_id(conn, project_id, 'E')
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO tasks (id, project_id, type, title, description, status, parent_id, created_at, updated_at) "
            "VALUES (?, ?, 'epic', ?, ?, 'todo', ?, ?, ?)",
            (epic_id, project_id, args.title, args.description, project_id, now, now)
        )
        conn.commit()
        print(f"Created epic: {epic_id} - {args.title}")
    finally:
        close_connection(conn)


def handle_list(args):
    conn = get_db(args)
    try:
        rows = conn.execute(
            "SELECT id, title, status FROM tasks WHERE type='epic' ORDER BY id"
        ).fetchall()
        if not rows:
            print("No epics found.")
            return
        for row in rows:
            check = 'x' if row['status'] == 'done' else ' '
            print(f"[{check}] {row['id']}: {row['title']} ({row['status']})")
    finally:
        close_connection(conn)


def handle_show(args):
    conn = get_db(args)
    try:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id=? AND type='epic'", (args.id,)
        ).fetchone()
        if row is None:
            print(f"Epic not found: {args.id}")
            raise SystemExit(1)
        print(f"Epic: {row['id']}")
        print(f"  Title: {row['title']}")
        print(f"  Status: {row['status']}")
        print(f"  Description: {row['description'] or '(none)'}")
        print(f"  Created: {row['created_at']}")
        print(f"  Updated: {row['updated_at']}")

        # Show child tasks
        children = conn.execute(
            "SELECT id, title, status FROM tasks WHERE parent_id=? AND type='task' ORDER BY seq_order, id",
            (args.id,)
        ).fetchall()
        if children:
            print(f"  Tasks ({len(children)}):")
            for child in children:
                check = 'x' if child['status'] == 'done' else ' '
                print(f"    [{check}] {child['id']}: {child['title']} ({child['status']})")
    finally:
        close_connection(conn)


def handle_update(args):
    conn = get_db(args)
    try:
        row = conn.execute("SELECT id FROM tasks WHERE id=? AND type='epic'", (args.id,)).fetchone()
        if row is None:
            print(f"Epic not found: {args.id}")
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

        if not updates:
            print("No updates specified.")
            return

        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        updates.append("updated_at=?")
        params.append(now)
        params.append(args.id)

        conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id=?", params)
        conn.commit()
        print(f"Updated epic: {args.id}")
    finally:
        close_connection(conn)


def handle_delete(args):
    conn = get_db(args)
    try:
        # Check for child tasks
        children = conn.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE parent_id=?", (args.id,)
        ).fetchone()
        if children['cnt'] > 0:
            print(f"Warning: Epic {args.id} has {children['cnt']} child task(s). Delete them first.")
            raise SystemExit(1)

        result = conn.execute("DELETE FROM tasks WHERE id=? AND type='epic'", (args.id,))
        conn.commit()
        if result.rowcount == 0:
            print(f"Epic not found: {args.id}")
            raise SystemExit(1)
        print(f"Deleted epic: {args.id}")
    finally:
        close_connection(conn)
