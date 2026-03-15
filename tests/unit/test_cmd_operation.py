"""Unit tests for operation command.
op 커맨드 유닛 테스트.
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


def setup_project_with_task(tmpdir):
    pp = os.path.join(tmpdir, 'test-proj')
    run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
    db = os.path.join(pp, 'taskops.db')
    run_cli('--db', db, 'epic', 'create', '--title', 'Epic A')
    run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task 1')
    return pp, db


def test_op_start():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        result = run_cli('--db', db, 'op', 'start', 'TST-T001', '--platform', 'claude_code')
        assert result.returncode == 0
        assert 'started' in result.stdout.lower()
        assert 'claude_code' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM operations WHERE task_id='TST-T001'").fetchone()
        assert row['operation_type'] == 'start'
        assert row['agent_platform'] == 'claude_code'
        assert row['started_at'] is not None
        conn.close()


def test_op_start_invalid_task():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        result = run_cli('--db', db, 'op', 'start', 'TST-T999')
        assert result.returncode == 1


def test_op_progress():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        run_cli('--db', db, 'op', 'start', 'TST-T001')
        result = run_cli('--db', db, 'op', 'progress', 'TST-T001',
                         '--summary', '2 of 3 endpoints done')
        assert result.returncode == 0
        assert '2 of 3' in result.stdout


def test_op_progress_with_subagent():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        run_cli('--db', db, 'op', 'progress', 'TST-T001',
                '--summary', 'Research done', '--subagent')

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT subagent_used FROM operations WHERE task_id='TST-T001' AND operation_type='progress'"
        ).fetchone()
        assert row['subagent_used'] == 1
        conn.close()


def test_op_progress_with_details():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        run_cli('--db', db, 'op', 'progress', 'TST-T001',
                '--summary', 'Files edited', '--details', '{"files":["auth.py"]}')

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT details FROM operations WHERE task_id='TST-T001' AND operation_type='progress'"
        ).fetchone()
        assert 'auth.py' in row['details']
        conn.close()


def test_op_complete():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        run_cli('--db', db, 'op', 'start', 'TST-T001')
        result = run_cli('--db', db, 'op', 'complete', 'TST-T001',
                         '--summary', 'Login API done')
        assert result.returncode == 0
        assert 'completed' in result.stdout.lower()

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM operations WHERE task_id='TST-T001' AND operation_type='complete'"
        ).fetchone()
        assert row['completed_at'] is not None
        conn.close()


def test_op_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        result = run_cli('--db', db, 'op', 'error', 'TST-T001',
                         '--summary', 'Build failed')
        assert result.returncode == 0
        assert 'error' in result.stdout.lower()


def test_op_interrupt():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        result = run_cli('--db', db, 'op', 'interrupt', 'TST-T001',
                         '--summary', 'Need API key')
        assert result.returncode == 0
        assert 'interrupt' in result.stdout.lower()


def test_op_log_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        run_cli('--db', db, 'op', 'start', 'TST-T001', '--platform', 'claude_code')
        run_cli('--db', db, 'op', 'progress', 'TST-T001', '--summary', 'Step 1 done')
        run_cli('--db', db, 'op', 'complete', 'TST-T001', '--summary', 'All done')

        result = run_cli('--db', db, 'op', 'log')
        assert 'start' in result.stdout
        assert 'progress' in result.stdout
        assert 'complete' in result.stdout


def test_op_log_filter_by_task():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        # Create a second task
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task 2')
        run_cli('--db', db, 'op', 'start', 'TST-T001')
        run_cli('--db', db, 'op', 'start', 'TST-T002')

        result = run_cli('--db', db, 'op', 'log', '--task', 'TST-T001')
        assert 'TST-T001' in result.stdout
        assert 'TST-T002' not in result.stdout


def test_op_log_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        result = run_cli('--db', db, 'op', 'log')
        assert 'No operations' in result.stdout
