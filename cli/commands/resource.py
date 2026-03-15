"""Resource management command.
Resource 관리 커맨드. 파일 경로 참조 및 중간 결과물 관리.
"""
from datetime import datetime
from .utils import get_db
from ..db.connection import close_connection


def register(subparsers):
    parser = subparsers.add_parser('resource', help='Manage resources')
    sub = parser.add_subparsers(dest='subcommand')

    add = sub.add_parser('add', help='Add a resource')
    add.add_argument('task_id', help='Task ID')
    add.add_argument('--path', required=True, help='File path')
    add.add_argument('--type', choices=['input', 'output', 'reference', 'intermediate'],
                     default='reference', dest='res_type', help='Resource type')
    add.add_argument('--desc', default='', help='Description')
    add.set_defaults(func=handle_add)

    lst = sub.add_parser('list', help='List resources')
    lst.add_argument('--task', help='Filter by task ID')
    lst.add_argument('--type', dest='res_type', help='Filter by type')
    lst.set_defaults(func=handle_list)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle_add(args):
    conn = get_db(args)
    try:
        row = conn.execute("SELECT id FROM tasks WHERE id=?", (args.task_id,)).fetchone()
        if row is None:
            print(f"Task not found: {args.task_id}")
            raise SystemExit(1)

        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO resources (task_id, file_path, description, res_type, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (args.task_id, args.path, args.desc, args.res_type, now)
        )
        conn.commit()
        print(f"Resource added: {args.path} ({args.res_type}) -> {args.task_id}")
    finally:
        close_connection(conn)


def handle_list(args):
    conn = get_db(args)
    try:
        query = "SELECT r.id, r.task_id, r.file_path, r.res_type, r.description FROM resources r"
        conditions = []
        params = []

        if args.task:
            conditions.append("r.task_id=?")
            params.append(args.task)
        if args.res_type:
            conditions.append("r.res_type=?")
            params.append(args.res_type)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY r.task_id, r.id"

        rows = conn.execute(query, params).fetchall()
        if not rows:
            print("No resources found.")
            return

        for row in rows:
            desc = f" - {row['description']}" if row['description'] else ""
            print(f"  [{row['res_type']}] {row['task_id']}: {row['file_path']}{desc}")
    finally:
        close_connection(conn)
