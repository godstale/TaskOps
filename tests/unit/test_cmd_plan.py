"""Unit tests for plan command.
plan 커맨드 유닛 테스트.
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}


def run_cli(*args):
    return subprocess.run(
        [sys.executable, '-m', 'cli', *args],
        capture_output=True, encoding='utf-8', errors='replace',
        cwd=PROJECT_ROOT, env=ENV
    )


def setup_project(tmpdir):
    pp = os.path.join(tmpdir, 'test-proj')
    run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
    db = os.path.join(pp, 'taskops.db')
    run_cli('--db', db, 'epic', 'create', '--title', 'Epic A')
    run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task 1')
    return pp, db


def test_plan_create_epic():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        changes = json.dumps({
            "create": [{"type": "epic", "title": "New Epic"}]
        })
        result = run_cli('--db', db, 'plan', 'update', '--changes', changes)
        assert result.returncode == 0
        assert 'TST-E002' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM tasks WHERE id='TST-E002'").fetchone()
        assert row is not None
        assert row['title'] == 'New Epic'
        assert row['type'] == 'epic'
        conn.close()


def test_plan_create_task():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        changes = json.dumps({
            "create": [{"type": "task", "title": "New Task", "parent_id": "TST-E001"}]
        })
        result = run_cli('--db', db, 'plan', 'update', '--changes', changes)
        assert result.returncode == 0
        assert 'TST-T002' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM tasks WHERE id='TST-T002'").fetchone()
        assert row is not None
        assert row['title'] == 'New Task'
        assert row['parent_id'] == 'TST-E001'
        conn.close()


def test_plan_create_invalid_parent_skipped():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        changes = json.dumps({
            "create": [{"type": "task", "title": "Bad Task", "parent_id": "TST-E999"}]
        })
        result = run_cli('--db', db, 'plan', 'update', '--changes', changes)
        assert result.returncode == 0
        assert 'Warning' in result.stdout

        conn = sqlite3.connect(db)
        count = conn.execute("SELECT COUNT(*) FROM tasks WHERE type='task'").fetchone()[0]
        assert count == 1  # only original Task 1
        conn.close()
