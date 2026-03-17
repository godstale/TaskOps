"""Project initialization command.
프로젝트 초기화 커맨드. 폴더, DB, 템플릿 파일을 생성.
"""
import os
from datetime import datetime
from string import Template

from ..db.connection import get_connection, close_connection


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')

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
    # --db flag takes precedence: derive project_path from the DB path
    if hasattr(args, 'db') and args.db:
        db_path = os.path.abspath(args.db)
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

    # Generate TASKOPS.md only
    template_vars = {
        'project_name': args.name,
        'prefix': args.prefix,
        'timestamp': now,
    }
    tmpl_path = os.path.join(TEMPLATE_DIR, 'TASKOPS.md.tmpl')
    out_path = os.path.join(project_path, 'TASKOPS.md')
    with open(tmpl_path, 'r', encoding='utf-8') as f:
        tmpl = Template(f.read())
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(tmpl.safe_substitute(template_vars))

    close_connection(conn)
    print(f"Project '{args.name}' initialized at {project_path}")
    print(f"  Prefix:  {args.prefix}")
    print(f"  DB:      {db_path}")
    print(f"  Guide:   {out_path}")
    print()
    print("Next step — add the following to your CLAUDE.md or AGENTS.md:")
    print("  @TASKOPS.md")
