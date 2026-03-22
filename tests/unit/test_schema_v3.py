"""Unit tests for schema v3 migration.
schema v3 마이그레이션 유닛 테스트.
"""
import os
import tempfile
import pytest
from cli.db.connection import get_connection, close_connection


def fresh_db():
    """Helper: create a fresh DB and return (conn, path)."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    conn = get_connection(db_path)
    return conn, db_path


def test_workflows_table_exists():
    conn, db_path = fresh_db()
    try:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        assert 'workflows' in tables, f"Expected 'workflows' table, got: {tables}"
    finally:
        close_connection(conn)
        os.unlink(db_path)


def test_tasks_has_workflow_id_column():
    conn, db_path = fresh_db()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(tasks)").fetchall()}
        assert 'workflow_id' in cols, f"Expected 'workflow_id' column, got: {cols}"
    finally:
        close_connection(conn)
        os.unlink(db_path)


def test_schema_version_is_3():
    conn, db_path = fresh_db()
    try:
        row = conn.execute(
            "SELECT value FROM settings WHERE key='__schema_version'"
        ).fetchone()
        assert row is not None, "No __schema_version in settings"
        assert int(row['value']) >= 3, f"Expected version >= 3, got {row['value']}"
    finally:
        close_connection(conn)
        os.unlink(db_path)


def test_workflows_table_columns():
    conn, db_path = fresh_db()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(workflows)").fetchall()}
        for expected in ('id', 'project_id', 'title', 'source_file', 'status', 'created_at'):
            assert expected in cols, f"Missing column '{expected}' in workflows"
    finally:
        close_connection(conn)
        os.unlink(db_path)


def test_next_workflow_id_first():
    conn, db_path = fresh_db()
    try:
        conn.execute(
            "INSERT INTO tasks (id, project_id, type, title, status) "
            "VALUES ('TST', 'TST', 'project', 'Test', 'in_progress')"
        )
        conn.commit()
        from cli.commands.utils import next_workflow_id
        wid = next_workflow_id(conn, 'TST', 'My Plan')
        assert wid == 'TST-MP'
    finally:
        close_connection(conn)
        os.unlink(db_path)


def test_next_workflow_id_unique_per_title():
    """Two different titles get different short IDs."""
    conn, db_path = fresh_db()
    try:
        conn.execute(
            "INSERT INTO tasks (id, project_id, type, title, status) "
            "VALUES ('TST', 'TST', 'project', 'Test', 'in_progress')"
        )
        conn.execute(
            "INSERT INTO workflows (id, project_id, title) VALUES ('TST-FW', 'TST', 'First')"
        )
        conn.commit()
        from cli.commands.utils import next_workflow_id
        wid = next_workflow_id(conn, 'TST', 'Alpha')
        assert wid == 'TST-AW'
    finally:
        close_connection(conn)
        os.unlink(db_path)


def test_v2_db_migration_adds_workflow_id_column():
    """Simulate a v2 DB (no workflow_id, no workflows table) and verify migration."""
    import sqlite3
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    # Build a raw v2-style DB manually (full v2 column set)
    raw = sqlite3.connect(db_path)
    raw.execute("""CREATE TABLE tasks (
        id TEXT PRIMARY KEY, project_id TEXT NOT NULL, type TEXT NOT NULL,
        title TEXT NOT NULL, description TEXT,
        status TEXT NOT NULL DEFAULT 'todo',
        parent_id TEXT, todo TEXT, interrupt TEXT,
        milestone_target TEXT, due_date TEXT,
        seq_order INTEGER, parallel_group TEXT, depends_on TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )""")
    raw.execute("""CREATE TABLE settings (
        key TEXT PRIMARY KEY, value TEXT NOT NULL, description TEXT, updated_at TEXT
    )""")
    raw.execute("INSERT INTO settings VALUES ('__schema_version','2','DB schema version',datetime('now'))")
    raw.commit()
    raw.close()

    # Now open through TaskOps connection (triggers migration)
    conn = get_connection(db_path)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(tasks)").fetchall()}
        assert 'workflow_id' in cols

        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        assert 'workflows' in tables

        row = conn.execute(
            "SELECT value FROM settings WHERE key='__schema_version'"
        ).fetchone()
        assert int(row['value']) >= 3
    finally:
        close_connection(conn)
        os.unlink(db_path)
