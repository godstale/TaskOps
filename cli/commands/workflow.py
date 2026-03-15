"""Workflow management command.
Workflow 관리 커맨드. 순차/병렬 실행 순서 및 의존성 관리.
"""
import json
from .utils import get_db
from ..db.connection import close_connection


def register(subparsers):
    parser = subparsers.add_parser('workflow', help='Manage workflow')
    sub = parser.add_subparsers(dest='subcommand')

    set_order = sub.add_parser('set-order', help='Set task execution order')
    set_order.add_argument('task_ids', nargs='+', help='Task IDs in order')
    set_order.set_defaults(func=handle_set_order)

    set_parallel = sub.add_parser('set-parallel', help='Set parallel execution group')
    set_parallel.add_argument('--group', required=True, help='Group name')
    set_parallel.add_argument('task_ids', nargs='+', help='Task IDs')
    set_parallel.set_defaults(func=handle_set_parallel)

    add_dep = sub.add_parser('add-dep', help='Add dependency')
    add_dep.add_argument('task_id', help='Task ID')
    add_dep.add_argument('--depends-on', nargs='+', required=True, help='Dependency task IDs')
    add_dep.set_defaults(func=handle_add_dep)

    show = sub.add_parser('show', help='Show workflow')
    show.set_defaults(func=handle_show)

    nxt = sub.add_parser('next', help='Show next executable tasks')
    nxt.set_defaults(func=handle_next)

    current = sub.add_parser('current', help='Show currently active task')
    current.set_defaults(func=handle_current)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle_set_order(args):
    conn = get_db(args)
    try:
        for i, task_id in enumerate(args.task_ids, start=1):
            row = conn.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row is None:
                print(f"Task not found: {task_id}")
                raise SystemExit(1)
            conn.execute("UPDATE tasks SET seq_order=? WHERE id=?", (i, task_id))
        conn.commit()
        print(f"Set execution order for {len(args.task_ids)} tasks:")
        for i, tid in enumerate(args.task_ids, start=1):
            print(f"  {i}. {tid}")
    finally:
        close_connection(conn)


def handle_set_parallel(args):
    conn = get_db(args)
    try:
        for task_id in args.task_ids:
            row = conn.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row is None:
                print(f"Task not found: {task_id}")
                raise SystemExit(1)
            conn.execute(
                "UPDATE tasks SET parallel_group=? WHERE id=?",
                (args.group, task_id)
            )
        conn.commit()
        print(f"Set parallel group '{args.group}' for: {', '.join(args.task_ids)}")
    finally:
        close_connection(conn)


def handle_add_dep(args):
    conn = get_db(args)
    try:
        row = conn.execute(
            "SELECT id, depends_on FROM tasks WHERE id=?", (args.task_id,)
        ).fetchone()
        if row is None:
            print(f"Task not found: {args.task_id}")
            raise SystemExit(1)

        # Validate dependency targets exist
        for dep_id in args.depends_on:
            dep = conn.execute("SELECT id FROM tasks WHERE id=?", (dep_id,)).fetchone()
            if dep is None:
                print(f"Dependency task not found: {dep_id}")
                raise SystemExit(1)

        # Merge with existing depends_on
        existing = json.loads(row['depends_on']) if row['depends_on'] else []
        for dep_id in args.depends_on:
            if dep_id not in existing:
                existing.append(dep_id)

        conn.execute(
            "UPDATE tasks SET depends_on=? WHERE id=?",
            (json.dumps(existing), args.task_id)
        )
        conn.commit()
        print(f"Task {args.task_id} now depends on: {', '.join(existing)}")
    finally:
        close_connection(conn)


def handle_show(args):
    conn = get_db(args)
    try:
        rows = conn.execute(
            "SELECT id, title, status, seq_order, parallel_group, depends_on "
            "FROM tasks WHERE type='task' AND seq_order IS NOT NULL "
            "ORDER BY seq_order, id"
        ).fetchall()

        if not rows:
            print("No workflow defined. Use 'workflow set-order' to define execution order.")
            return

        print("Workflow:")
        current_order = None
        for row in rows:
            order = row['seq_order']
            check = 'x' if row['status'] == 'done' else ' '
            group = f" [group: {row['parallel_group']}]" if row['parallel_group'] else ""
            deps = ""
            if row['depends_on']:
                dep_list = json.loads(row['depends_on'])
                deps = f" (depends: {', '.join(dep_list)})"

            if order != current_order:
                current_order = order
                print(f"  {order}. [{check}] {row['id']}: {row['title']} ({row['status']}){group}{deps}")
            else:
                print(f"     [{check}] {row['id']}: {row['title']} ({row['status']}){group}{deps}")
    finally:
        close_connection(conn)


def _deps_satisfied(conn, depends_on_json):
    """Check if all dependencies are done. Python-based for compatibility."""
    if not depends_on_json:
        return True
    dep_ids = json.loads(depends_on_json)
    if not dep_ids:
        return True
    placeholders = ','.join('?' for _ in dep_ids)
    row = conn.execute(
        f"SELECT COUNT(*) as cnt FROM tasks WHERE id IN ({placeholders}) AND status != 'done'",
        dep_ids
    ).fetchone()
    return row['cnt'] == 0


def handle_next(args):
    conn = get_db(args)
    try:
        rows = conn.execute(
            "SELECT id, title, seq_order, parallel_group, depends_on FROM tasks "
            "WHERE status = 'todo' AND type = 'task' "
            "ORDER BY seq_order ASC, id ASC"
        ).fetchall()

        executable = []
        for row in rows:
            if _deps_satisfied(conn, row['depends_on']):
                executable.append(row)

        if not executable:
            print("No executable tasks. All tasks may be done or blocked.")
            return

        print("Next executable tasks:")
        for row in executable:
            group = f" [group: {row['parallel_group']}]" if row['parallel_group'] else ""
            print(f"  {row['id']}: {row['title']}{group}")
    finally:
        close_connection(conn)


def handle_current(args):
    conn = get_db(args)
    try:
        row = conn.execute(
            "SELECT id FROM tasks WHERE status='in_progress' AND type='task' "
            "ORDER BY seq_order, id LIMIT 1"
        ).fetchone()
        if row is None:
            # No output for scripting use (hooks)
            return
        print(row['id'])
    finally:
        close_connection(conn)
