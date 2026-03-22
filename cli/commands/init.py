"""Project initialization command.
프로젝트 초기화 커맨드. 폴더와 DB를 생성.
"""
import os
from datetime import datetime

from ..db.connection import get_connection, close_connection

DEFAULT_SETTINGS = [
    ('autonomy_level', 'moderate', 'Agent autonomy level (low|moderate|high)'),
    ('commit_style', 'conventional', 'Commit message style'),
    ('use_subagent', 'true', 'Allow sub agent usage'),
    ('parallel_execution', 'true', 'Allow parallel task execution'),
    ('progress_interval', 'major_steps', 'Progress log interval (every_tool|major_steps|start_end_only)'),
]


def register(subparsers):
    parser = subparsers.add_parser('init', help='Initialize a new project')
    parser.add_argument('--name', required=True, help='Project name')
    parser.add_argument('--prefix', required=True, help='Task ID prefix (e.g. TOS)')
    parser.add_argument('--path', default='.', help='Project folder path (default: cwd)')
    parser.set_defaults(func=handle)


def handle(args):
    # Priority: --db flag > TASKOPS_DB env var > --path argument
    if hasattr(args, 'db') and args.db:
        db_path = os.path.abspath(args.db)
        project_path = os.path.dirname(db_path)
    elif os.environ.get('TASKOPS_DB'):
        db_path = os.path.abspath(os.environ['TASKOPS_DB'])
        project_path = os.path.dirname(db_path)
    else:
        project_path = os.path.abspath(args.path)
        db_path = os.path.join(project_path, 'taskops.db')
    os.makedirs(project_path, exist_ok=True)
    conn = get_connection(db_path)

    now = datetime.now().isoformat(sep=' ', timespec='seconds')

    # Insert project record
    conn.execute(
        "INSERT OR IGNORE INTO tasks (id, project_id, type, title, status, created_at, updated_at) "
        "VALUES (?, ?, 'project', ?, 'in_progress', ?, ?)",
        (args.prefix, args.prefix, args.name, now, now)
    )

    # Insert default settings
    for key, value, desc in DEFAULT_SETTINGS:
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value, description, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (key, value, desc, now)
        )
    conn.commit()

    close_connection(conn)
    print(f"Project '{args.name}' initialized.")
    print(f"  Prefix:  {args.prefix}")
    print(f"  DB:      {db_path}")
