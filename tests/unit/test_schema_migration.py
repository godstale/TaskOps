"""Tests for DB schema migration v1 -> v2.
DB 스키마 마이그레이션 v1 -> v2 테스트.
"""
import os
import sqlite3
import tempfile


V1_CREATE_OPERATIONS = """
CREATE TABLE operations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT NOT NULL,
    operation_type  TEXT NOT NULL,
    agent_platform  TEXT,
    summary         TEXT,
    details         TEXT,
    subagent_used   INTEGER DEFAULT 0,
    subagent_result TEXT,
    started_at      TEXT,
    completed_at    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

V1_CREATE_SETTINGS = """
CREATE TABLE settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    description TEXT,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

V1_CREATE_TASKS = """
CREATE TABLE tasks (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL,
    type        TEXT NOT NULL,
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'todo',
    parent_id   TEXT,
    todo        TEXT,
    interrupt   TEXT,
    milestone_target TEXT,
    due_date    TEXT,
    seq_order   INTEGER,
    parallel_group TEXT,
    depends_on  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


def create_v1_db(path):
    conn = sqlite3.connect(path)
    conn.execute(V1_CREATE_TASKS)
    conn.execute(V1_CREATE_OPERATIONS)
    conn.execute(V1_CREATE_SETTINGS)
    conn.execute("CREATE TABLE resources (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL, file_path TEXT NOT NULL, description TEXT, res_type TEXT NOT NULL DEFAULT 'reference', created_at TEXT NOT NULL DEFAULT (datetime('now')))")
    conn.execute("CREATE TABLE checkpoints (id INTEGER PRIMARY KEY AUTOINCREMENT, note TEXT, snapshot TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')))")
    conn.commit()
    conn.close()


NEW_COLUMNS = [
    'tool_name', 'skill_name', 'mcp_name',
    'retry_count', 'input_tokens', 'output_tokens', 'duration_seconds'
]


def test_migrate_v1_to_v2_adds_columns():
    from cli.db.connection import get_connection, close_connection
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'v1.db')
        create_v1_db(db_path)
        conn = get_connection(db_path)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(operations)").fetchall()}
        for col in NEW_COLUMNS:
            assert col in cols, f"Column '{col}' not found after migration"
        close_connection(conn)


def test_migrate_v1_to_v2_sets_schema_version():
    from cli.db.connection import get_connection, close_connection
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'v1.db')
        create_v1_db(db_path)
        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT value FROM settings WHERE key='__schema_version'"
        ).fetchone()
        assert row is not None
        assert row[0] == '2'
        close_connection(conn)


def test_fresh_install_has_new_columns():
    from cli.db.connection import get_connection, close_connection
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'fresh.db')
        conn = get_connection(db_path)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(operations)").fetchall()}
        for col in NEW_COLUMNS:
            assert col in cols, f"Column '{col}' not in fresh install"
        close_connection(conn)


def test_migrate_idempotent():
    from cli.db.connection import get_connection, close_connection
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        conn = get_connection(db_path)
        close_connection(conn)
        conn2 = get_connection(db_path)
        close_connection(conn2)
