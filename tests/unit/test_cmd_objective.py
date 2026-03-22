"""Unit tests for objective command.
objective 커맨드 유닛 테스트.
"""
import os
import subprocess
import sys
import sqlite3
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
    return pp, db


def test_objective_create_milestone():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'objective', 'create',
                         '--title', 'MVP Complete', '--milestone', 'Core 3 features done',
                         '--workflow', 'TST-TW')
        assert result.returncode == 0
        assert 'TW-O001' in result.stdout
        assert 'Milestone' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM tasks WHERE id='TW-O001'").fetchone()
        assert row['type'] == 'objective'
        assert row['milestone_target'] == 'Core 3 features done'
        assert row['due_date'] is None
        conn.close()


def test_objective_create_due_date():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'objective', 'create',
                         '--title', 'Demo Day', '--due-date', '2026-03-20',
                         '--workflow', 'TST-TW')
        assert result.returncode == 0
        assert 'TW-O001' in result.stdout
        assert '2026-03-20' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM tasks WHERE id='TW-O001'").fetchone()
        assert row['due_date'] == '2026-03-20'
        conn.close()


def test_objective_create_both():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'objective', 'create',
                         '--title', 'Release', '--milestone', 'All tests pass',
                         '--due-date', '2026-04-01', '--workflow', 'TST-TW')
        assert result.returncode == 0
        assert 'TW-O001' in result.stdout


def test_objective_sequential_ids():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        run_cli('--db', db, 'objective', 'create', '--title', 'Obj 1', '--workflow', 'TST-TW')
        run_cli('--db', db, 'objective', 'create', '--title', 'Obj 2', '--workflow', 'TST-TW')
        result = run_cli('--db', db, 'objective', 'create', '--title', 'Obj 3', '--workflow', 'TST-TW')
        assert 'TW-O003' in result.stdout


def test_objective_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        run_cli('--db', db, 'objective', 'create',
                '--title', 'MVP', '--milestone', 'Core features', '--workflow', 'TST-TW')
        run_cli('--db', db, 'objective', 'create',
                '--title', 'Demo', '--due-date', '2026-03-20', '--workflow', 'TST-TW')
        result = run_cli('--db', db, 'objective', 'list')
        assert 'MVP' in result.stdout
        assert 'Demo' in result.stdout
        assert 'milestone' in result.stdout
        assert 'due' in result.stdout


def test_objective_list_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'objective', 'list')
        assert 'No objectives' in result.stdout


def test_objective_update_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        run_cli('--db', db, 'objective', 'create', '--title', 'MVP', '--workflow', 'TST-TW')
        result = run_cli('--db', db, 'objective', 'update', 'TW-O001', '--status', 'done')
        assert result.returncode == 0

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status FROM tasks WHERE id='TW-O001'").fetchone()
        assert row['status'] == 'done'
        conn.close()


def test_objective_update_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'objective', 'update', 'TST-O999', '--status', 'done')
        assert result.returncode == 1


def test_objective_delete():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        run_cli('--db', db, 'objective', 'create', '--title', 'MVP', '--workflow', 'TST-TW')
        result = run_cli('--db', db, 'objective', 'delete', 'TW-O001')
        assert result.returncode == 0
        assert 'Deleted' in result.stdout


def test_objective_delete_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'objective', 'delete', 'TST-O999')
        assert result.returncode == 1
