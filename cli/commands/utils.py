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


def next_workflow_id(conn, project_prefix, title):
    """Generate workflow ID using title-derived short string.
    제목 기반 단축 문자열로 워크플로우 ID 생성.
    """
    short = generate_workflow_short(title, conn)
    return f"{project_prefix}-{short}"


def generate_workflow_short(title: str, conn) -> str:
    """Derive a unique 2-4 char uppercase ASCII short string from a workflow title.
    워크플로우 제목에서 고유한 2-4자 대문자 ASCII 단축 문자열 생성.
    """
    import re
    words = re.split(r'[^A-Za-z0-9]+', title)
    base = ''.join(w[0] for w in words if w and w[0].isupper() and ord(w[0]) < 128)
    while len(base) < 2:
        base += 'W'
    base = base[:4]

    existing = set()
    rows = conn.execute("SELECT id FROM workflows").fetchall()
    for row in rows:
        wf_id = row['id'] if isinstance(row, dict) else row[0]
        if '-' in wf_id:
            existing.add(wf_id.split('-', 1)[1])

    if base not in existing:
        return base

    stem = base[:3]
    for i in range(1, 100):
        candidate = f"{stem}{i}"
        if candidate not in existing:
            return candidate
    return base  # unreachable in practice


def get_workflow_prefix(workflow_id: str) -> str:
    """Extract short prefix from a workflow ID.
    워크플로우 ID에서 단축 프리픽스 추출.
    'SMR-RTS1' -> 'RTS1', 'PRJ-W001' -> 'W001'
    """
    return workflow_id.split('-', 1)[1]


def get_project_dir(args):
    """Get the project directory (where taskops.db lives).
    프로젝트 디렉토리 (taskops.db가 있는 곳) 반환.
    """
    db_path = resolve_db_path(args)
    return os.path.dirname(db_path)
