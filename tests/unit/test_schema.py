"""Unit tests for DB schema.
DB 스키마 유닛 테스트.
"""
import sqlite3
import os
import tempfile
from cli.db.schema import create_tables, SCHEMA_VERSION


def test_schema_version_exists():
    assert isinstance(SCHEMA_VERSION, int)
    assert SCHEMA_VERSION >= 1


def test_create_tables_creates_all_tables():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        conn = sqlite3.connect(db_path)
        create_tables(conn)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert 'tasks' in tables
        assert 'operations' in tables
        assert 'resources' in tables
        assert 'settings' in tables
        conn.close()
    finally:
        os.unlink(db_path)


def test_create_tables_creates_indexes():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        conn = sqlite3.connect(db_path)
        create_tables(conn)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indexes = [row[0] for row in cursor.fetchall()]
        assert 'idx_tasks_project' in indexes
        assert 'idx_tasks_parent' in indexes
        assert 'idx_tasks_type' in indexes
        assert 'idx_tasks_status' in indexes
        assert 'idx_operations_task' in indexes
        assert 'idx_resources_task' in indexes
        conn.close()
    finally:
        os.unlink(db_path)


def test_create_tables_is_idempotent():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        conn = sqlite3.connect(db_path)
        create_tables(conn)
        create_tables(conn)  # should not raise
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert 'tasks' in tables
        conn.close()
    finally:
        os.unlink(db_path)


def test_tasks_table_constraints():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys=ON;")
        create_tables(conn)

        # Valid insert
        conn.execute(
            "INSERT INTO tasks (id, project_id, type, title) VALUES ('T1', 'PRJ', 'task', 'Test')"
        )
        conn.commit()

        # Invalid type should fail
        import pytest
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO tasks (id, project_id, type, title) VALUES ('T2', 'PRJ', 'invalid', 'Test')"
            )

        # Invalid status should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO tasks (id, project_id, type, title, status) VALUES ('T3', 'PRJ', 'task', 'Test', 'bad')"
            )

        conn.close()
    finally:
        os.unlink(db_path)
