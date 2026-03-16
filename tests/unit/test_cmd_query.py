"""Unit tests for query command.
query 커맨드 유닛 테스트.
"""
import os
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


def setup_full_project(tmpdir):
    """Create a project with epics, tasks, objectives, and operations."""
    pp = os.path.join(tmpdir, 'test-proj')
    run_cli('init', '--name', 'Test Project', '--prefix', 'TST', '--path', pp)
    db = os.path.join(pp, 'taskops.db')

    run_cli('--db', db, 'epic', 'create', '--title', 'Auth System')
    run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001',
            '--title', 'Login API', '--description', 'Implement login endpoint')
    run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Signup API')
    run_cli('--db', db, 'task', 'create', '--parent', 'TST-T001', '--title', 'JWT Token')

    run_cli('--db', db, 'task', 'update', 'TST-T001', '--status', 'done')

    run_cli('--db', db, 'objective', 'create',
            '--title', 'MVP Complete', '--milestone', 'Core features done')

    run_cli('--db', db, 'workflow', 'set-order', 'TST-T001', 'TST-T002', 'TST-T003')

    run_cli('--db', db, 'op', 'start', 'TST-T001', '--platform', 'claude_code')
    run_cli('--db', db, 'op', 'progress', 'TST-T001', '--summary', 'Halfway done')
    run_cli('--db', db, 'op', 'complete', 'TST-T001', '--summary', 'Login API done')

    return pp, db


def test_query_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_full_project(tmpdir)
        result = run_cli('--db', db, 'query', 'status')
        assert result.returncode == 0
        assert 'Test Project' in result.stdout
        assert 'Epics: 1' in result.stdout
        assert 'Tasks: 3' in result.stdout
        assert 'Objectives: 1' in result.stdout
        assert 'done: 1' in result.stdout


def test_query_status_progress_percentage():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_full_project(tmpdir)
        result = run_cli('--db', db, 'query', 'status')
        assert '1/3' in result.stdout
        assert '33%' in result.stdout


def test_query_tasks_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_full_project(tmpdir)
        result = run_cli('--db', db, 'query', 'tasks')
        assert 'Login API' in result.stdout
        assert 'Signup API' in result.stdout
        assert 'JWT Token' in result.stdout


def test_query_tasks_filter_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_full_project(tmpdir)
        result = run_cli('--db', db, 'query', 'tasks', '--status', 'todo')
        assert 'Login API' not in result.stdout
        assert 'Signup API' in result.stdout


def test_query_show_stdout():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_full_project(tmpdir)
        result = run_cli('--db', db, 'query', 'show')
        assert result.returncode == 0
        assert 'TST-T001' in result.stdout
        assert 'Auth System' in result.stdout
        assert 'Login API' in result.stdout


def test_query_show_no_file_written():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_full_project(tmpdir)
        # Remove any TODO.md created by init, then verify query show does not recreate it
        todo_path = os.path.join(pp, 'TODO.md')
        if os.path.exists(todo_path):
            os.remove(todo_path)
        run_cli('--db', db, 'query', 'show')
        assert not os.path.exists(todo_path)


def test_query_show_workflow_filter():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_full_project(tmpdir)
        run_cli('--db', db, 'workflow', 'create', '--title', 'W1')
        result = run_cli('--db', db, 'query', 'show', '--workflow', 'TST-W001')
        assert result.returncode == 0


def test_query_show_parallel_group():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_full_project(tmpdir)
        run_cli('--db', db, 'workflow', 'set-parallel',
                '--group', 'auth-grp', 'TST-T002', 'TST-T003')
        result = run_cli('--db', db, 'query', 'show')
        assert 'auth-grp' in result.stdout


def test_query_show_subtasks():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_full_project(tmpdir)
        result = run_cli('--db', db, 'query', 'show')
        assert 'JWT Token' in result.stdout


def test_query_show_objectives():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_full_project(tmpdir)
        result = run_cli('--db', db, 'query', 'show')
        assert 'MVP Complete' in result.stdout
