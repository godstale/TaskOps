"""Shared utilities for commands.
커맨드 공통 유틸리티.
"""
import os
from ..db.connection import get_connection, close_connection


def resolve_db_path(args):
    """Resolve DB path from --db flag, TASKOPS_DB env var, or cwd search.
    --db 플래그, TASKOPS_DB 환경변수, 또는 현재 디렉토리 탐색으로 DB 경로 결정.
    """
    if hasattr(args, 'db') and args.db:
        return args.db
    env_db = os.environ.get('TASKOPS_DB')
    if env_db:
        return env_db
    # Search for taskops.db in current directory and parents
    cwd = os.getcwd()
    path = cwd
    while True:
        candidate = os.path.join(path, 'taskops.db')
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    return os.path.join(cwd, 'taskops.db')


def get_db(args):
    """Get DB connection using resolved path.
    DB 연결을 가져옴.
    """
    db_path = resolve_db_path(args)
    if not os.path.exists(db_path):
        print(f"Error: DB not found at {db_path}. Run 'taskops init' first.")
        raise SystemExit(1)
    return get_connection(db_path)


def get_project_id(conn):
    """Get the project ID from the DB.
    DB에서 프로젝트 ID를 가져옴.
    """
    row = conn.execute("SELECT id FROM tasks WHERE type='project' LIMIT 1").fetchone()
    if row is None:
        print("Error: No project found in DB. Run 'taskops init' first.")
        raise SystemExit(1)
    return row['id']


def next_id(conn, prefix, type_char):
    """Generate next sequential ID for a given type.
    주어진 타입의 다음 순차 ID 생성.
    type_char: 'E' for epic, 'T' for task, 'O' for objective
    """
    pattern = f"{prefix}-{type_char}%"
    row = conn.execute(
        "SELECT id FROM tasks WHERE id LIKE ? ORDER BY id DESC LIMIT 1",
        (pattern,)
    ).fetchone()
    if row is None:
        return f"{prefix}-{type_char}001"
    # Extract numeric part
    current_id = row['id']
    num_str = current_id.split(f'-{type_char}')[1]
    next_num = int(num_str) + 1
    return f"{prefix}-{type_char}{next_num:03d}"


def next_workflow_id(conn, prefix):
    """Generate next sequential workflow ID.
    다음 순차 Workflow ID 생성. e.g. PRJ-W001, PRJ-W002
    """
    pattern = f"{prefix}-W%"
    row = conn.execute(
        "SELECT id FROM workflows WHERE id LIKE ? ORDER BY id DESC LIMIT 1",
        (pattern,)
    ).fetchone()
    if row is None:
        return f"{prefix}-W001"
    num_str = row['id'].split('-W')[1]
    return f"{prefix}-W{int(num_str) + 1:03d}"


def get_project_dir(args):
    """Get the project directory (where taskops.db lives).
    프로젝트 디렉토리 (taskops.db가 있는 곳) 반환.
    """
    db_path = resolve_db_path(args)
    return os.path.dirname(db_path)
