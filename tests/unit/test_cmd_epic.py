"""Unit tests for epic command.
epic 커맨드 유닛 테스트.
"""
import os
import subprocess
import sys
import sqlite3
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, '-m', 'cli', *args],
        capture_output=True, encoding='utf-8', errors='replace',
        cwd=cwd or PROJECT_ROOT, env=ENV
    )


def setup_project(tmpdir):
    """Initialize a project and return the path."""
    project_path = os.path.join(tmpdir, 'test-proj')
    run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', project_path)
    return project_path


def test_epic_create():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp = setup_project(tmpdir)
        result = run_cli('--db', os.path.join(pp, 'taskops.db'),
                         'epic', 'create', '--title', 'Auth System')
        assert result.returncode == 0
        assert 'TST-E001' in result.stdout

        conn = sqlite3.connect(os.path.join(pp, 'taskops.db'))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM tasks WHERE id='TST-E001'").fetchone()
        assert row['type'] == 'epic'
        assert row['title'] == 'Auth System'
        assert row['status'] == 'todo'
        conn.close()


def test_epic_create_sequential_ids():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp = setup_project(tmpdir)
        db = os.path.join(pp, 'taskops.db')
        run_cli('--db', db, 'epic', 'create', '--title', 'Epic 1')
        run_cli('--db', db, 'epic', 'create', '--title', 'Epic 2')
        result = run_cli('--db', db, 'epic', 'create', '--title', 'Epic 3')
        assert 'TST-E003' in result.stdout


def test_epic_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp = setup_project(tmpdir)
        db = os.path.join(pp, 'taskops.db')
        run_cli('--db', db, 'epic', 'create', '--title', 'Epic A')
        run_cli('--db', db, 'epic', 'create', '--title', 'Epic B')
        result = run_cli('--db', db, 'epic', 'list')
        assert 'TST-E001' in result.stdout
        assert 'Epic A' in result.stdout
        assert 'TST-E002' in result.stdout
        assert 'Epic B' in result.stdout


def test_epic_show():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp = setup_project(tmpdir)
        db = os.path.join(pp, 'taskops.db')
        run_cli('--db', db, 'epic', 'create', '--title', 'My Epic', '--description', 'Detailed desc')
        result = run_cli('--db', db, 'epic', 'show', 'TST-E001')
        assert 'My Epic' in result.stdout
        assert 'Detailed desc' in result.stdout


def test_epic_show_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp = setup_project(tmpdir)
        db = os.path.join(pp, 'taskops.db')
        result = run_cli('--db', db, 'epic', 'show', 'TST-E999')
        assert result.returncode == 1


def test_epic_update_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp = setup_project(tmpdir)
        db = os.path.join(pp, 'taskops.db')
        run_cli('--db', db, 'epic', 'create', '--title', 'My Epic')
        result = run_cli('--db', db, 'epic', 'update', 'TST-E001', '--status', 'in_progress')
        assert result.returncode == 0

        conn = sqlite3.connect(os.path.join(pp, 'taskops.db'))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status FROM tasks WHERE id='TST-E001'").fetchone()
        assert row['status'] == 'in_progress'
        conn.close()


def test_epic_delete():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp = setup_project(tmpdir)
        db = os.path.join(pp, 'taskops.db')
        run_cli('--db', db, 'epic', 'create', '--title', 'My Epic')
        result = run_cli('--db', db, 'epic', 'delete', 'TST-E001')
        assert result.returncode == 0
        assert 'Deleted' in result.stdout


def test_epic_delete_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp = setup_project(tmpdir)
        db = os.path.join(pp, 'taskops.db')
        result = run_cli('--db', db, 'epic', 'delete', 'TST-E999')
        assert result.returncode == 1
