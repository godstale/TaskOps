"""Unit tests for DB connection.
DB 연결 유닛 테스트.
"""
import os
import tempfile
from cli.db.connection import get_connection, close_connection


def test_get_connection_creates_db_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        conn = get_connection(db_path)
        assert os.path.exists(db_path)
        close_connection(conn)


def test_get_connection_initializes_tables():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        conn = get_connection(db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert 'tasks' in tables
        assert 'operations' in tables
        assert 'resources' in tables
        assert 'settings' in tables
        close_connection(conn)


def test_get_connection_enables_row_factory():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        conn = get_connection(db_path)
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('test_key', 'test_val')"
        )
        conn.commit()
        row = conn.execute("SELECT * FROM settings WHERE key='test_key'").fetchone()
        # Row factory allows dict-like access
        assert row['key'] == 'test_key'
        assert row['value'] == 'test_val'
        close_connection(conn)


def test_get_connection_enables_foreign_keys():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        conn = get_connection(db_path)
        result = conn.execute("PRAGMA foreign_keys;").fetchone()
        assert result[0] == 1
        close_connection(conn)


def test_close_connection_handles_none():
    close_connection(None)  # should not raise
