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
    run_cli('--db', db, 'workflow', 'create', '--title', 'Test Workflow')
    run_cli('--db', db, 'epic', 'create', '--title', 'Epic A', '--workflow', 'TST-TW')
    run_cli('--db', db, 'task', 'create', '--parent', 'TW-E001', '--title', 'Task 1', '--workflow', 'TST-TW')
    return pp, db


def test_plan_create_epic():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        changes = json.dumps({
            "create": [{"type": "epic", "title": "New Epic"}]
        })
        result = run_cli('--db', db, 'plan', 'update', '--changes', changes, '--workflow', 'TST-TW')
        assert result.returncode == 0
        assert 'TW-E002' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM tasks WHERE id='TW-E002'").fetchone()
        assert row is not None
        assert row['title'] == 'New Epic'
        assert row['type'] == 'epic'
        conn.close()


def test_plan_create_task():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        changes = json.dumps({
            "create": [{"type": "task", "title": "New Task", "parent_id": "TW-E001"}]
        })
        result = run_cli('--db', db, 'plan', 'update', '--changes', changes, '--workflow', 'TST-TW')
        assert result.returncode == 0
        assert 'TW-T002' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM tasks WHERE id='TW-T002'").fetchone()
        assert row is not None
        assert row['title'] == 'New Task'
        assert row['parent_id'] == 'TW-E001'
        conn.close()


def test_plan_create_invalid_parent_skipped():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        changes = json.dumps({
            "create": [{"type": "task", "title": "Bad Task", "parent_id": "TST-E999"}]
        })
        result = run_cli('--db', db, 'plan', 'update', '--changes', changes, '--workflow', 'TST-TW')
        assert result.returncode == 0
        assert 'Warning' in result.stdout

        conn = sqlite3.connect(db)
        count = conn.execute("SELECT COUNT(*) FROM tasks WHERE type='task'").fetchone()[0]
        assert count == 1  # only original Task 1
        conn.close()


def test_plan_update_task():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        changes = json.dumps({
            "update": [{"id": "TW-T001", "title": "Renamed Task", "status": "done"}]
        })
        result = run_cli('--db', db, 'plan', 'update', '--changes', changes)
        assert result.returncode == 0
        assert 'TW-T001' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT title, status FROM tasks WHERE id='TW-T001'").fetchone()
        assert row['title'] == 'Renamed Task'
        assert row['status'] == 'done'
        conn.close()


def test_plan_update_unknown_id_skipped():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        changes = json.dumps({
            "update": [{"id": "TST-T999", "title": "Ghost"}]
        })
        result = run_cli('--db', db, 'plan', 'update', '--changes', changes)
        assert result.returncode == 0
        assert 'Warning' in result.stdout


def test_plan_delete_task():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        # Create a subtask under TW-T001
        run_cli('--db', db, 'task', 'create', '--parent', 'TW-T001', '--title', 'Subtask', '--workflow', 'TST-TW')

        changes = json.dumps({
            "delete": [{"id": "TW-T001"}]
        })
        result = run_cli('--db', db, 'plan', 'update', '--changes', changes)
        assert result.returncode == 0
        assert 'TW-T001' in result.stdout

        conn = sqlite3.connect(db)
        # Both TW-T001 and its subtask (TW-T002) should be gone
        count = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE id IN ('TW-T001', 'TW-T002')"
        ).fetchone()[0]
        assert count == 0
        conn.close()


def test_plan_delete_unknown_id_skipped():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        changes = json.dumps({
            "delete": [{"id": "TST-T999"}]
        })
        result = run_cli('--db', db, 'plan', 'update', '--changes', changes)
        assert result.returncode == 0
        assert 'Warning' in result.stdout


def test_plan_empty_changes():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'plan', 'update', '--changes', '{}')
        assert result.returncode == 0
        assert 'No changes applied' in result.stdout


def test_plan_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'plan', 'update', '--changes', 'not-json')
        assert result.returncode == 1
        assert 'Error' in result.stdout


def test_plan_update_does_not_regenerate_todo_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        # Remove any TODO.md created by init
        todo_path = os.path.join(pp, 'TODO.md')
        if os.path.exists(todo_path):
            os.remove(todo_path)
        changes = json.dumps({
            "create": [{"type": "task", "title": "New Task", "parent_id": "TW-E001"}]
        })
        result = run_cli('--db', db, 'plan', 'update', '--changes', changes, '--workflow', 'TST-TW')
        assert result.returncode == 0
        # plan update should NOT write TODO.md anymore
        assert not os.path.exists(todo_path)


def test_plan_update_from_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        changes_file = os.path.join(tmpdir, 'changes.json')
        changes = {"create": [{"type": "epic", "title": "Epic from file"}]}
        with open(changes_file, 'w', encoding='utf-8') as f:
            json.dump(changes, f)

        result = run_cli('--db', db, 'plan', 'update', '--changes-file', changes_file, '--workflow', 'TST-TW')
        assert result.returncode == 0
        assert 'TW-E002' in result.stdout


def test_plan_delete_task_with_operations():
    """Deleting a task with associated operations should not raise FK error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        # Add an operation to TW-T001
        run_cli('--db', db, 'op', 'start', 'TW-T001', '--platform', 'test')

        changes = json.dumps({"delete": [{"id": "TW-T001"}]})
        result = run_cli('--db', db, 'plan', 'update', '--changes', changes)
        assert result.returncode == 0
        assert 'TW-T001' in result.stdout

        conn = sqlite3.connect(db)
        assert conn.execute("SELECT COUNT(*) FROM tasks WHERE id='TW-T001'").fetchone()[0] == 0
        conn.close()
