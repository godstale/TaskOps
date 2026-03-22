"""Setting management command.
설정 관리 커맨드.
"""
from datetime import datetime
from .utils import get_db
from ..db.connection import close_connection


def register(subparsers):
    parser = subparsers.add_parser('setting', help='Manage settings')
    sub = parser.add_subparsers(dest='subcommand')

    s = sub.add_parser('set', help='Set a setting value')
    s.add_argument('key', help='Setting key')
    s.add_argument('value', help='Setting value')
    s.add_argument('--desc', default='', help='Description')
    s.set_defaults(func=handle_set)

    g = sub.add_parser('get', help='Get a setting value')
    g.add_argument('key', help='Setting key')
    g.set_defaults(func=handle_get)

    lst = sub.add_parser('list', help='List all settings')
    lst.set_defaults(func=handle_list)

    d = sub.add_parser('delete', help='Delete a setting')
    d.add_argument('key', help='Setting key')
    d.set_defaults(func=handle_delete)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle_set(args):
    conn = get_db(args)
    try:
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO settings (key, value, description, updated_at) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=?, description=?, updated_at=?",
            (args.key, args.value, args.desc, now,
             args.value, args.desc, now)
        )
        conn.commit()
        print(f"Setting set: {args.key} = {args.value}")
    finally:
        close_connection(conn)


def handle_get(args):
    conn = get_db(args)
    try:
        row = conn.execute(
            "SELECT value, description FROM settings WHERE key=?", (args.key,)
        ).fetchone()
        if row is None:
            print(f"Setting not found: {args.key}")
            raise SystemExit(1)
        desc = f"  # {row['description']}" if row['description'] else ""
        print(f"{args.key} = {row['value']}{desc}")
    finally:
        close_connection(conn)


def handle_list(args):
    conn = get_db(args)
    try:
        rows = conn.execute(
            "SELECT key, value, description FROM settings ORDER BY key"
        ).fetchall()
        if not rows:
            print("No settings found.")
            return
        for row in rows:
            desc = f"  # {row['description']}" if row['description'] else ""
            print(f"  {row['key']} = {row['value']}{desc}")
    finally:
        close_connection(conn)


def handle_delete(args):
    conn = get_db(args)
    try:
        result = conn.execute("DELETE FROM settings WHERE key=?", (args.key,))
        conn.commit()
        if result.rowcount == 0:
            print(f"Setting not found: {args.key}")
            raise SystemExit(1)
        print(f"Setting deleted: {args.key}")
    finally:
        close_connection(conn)
