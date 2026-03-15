"""Unit tests for task command.
task 커맨드 유닛 테스트.
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


def setup_project_with_epic(tmpdir):
    """Initialize project and create one epic."""
    pp = os.path.join(tmpdir, 'test-proj')
    run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
    db = os.path.join(pp, 'taskops.db')
    run_cli('--db', db, 'epic', 'create', '--title', 'Test Epic')
    return pp, db


def test_task_create():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_epic(tmpdir)
        result = run_cli('--db', db, 'task', 'create',
                         '--parent', 'TST-E001', '--title', 'Login API')
        assert result.returncode == 0
        assert 'TST-T001' in result.stdout
        assert 'task' in result.stdout.lower()


def test_task_create_subtask():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_epic(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Parent Task')
        result = run_cli('--db', db, 'task', 'create',
                         '--parent', 'TST-T001', '--title', 'Sub Task')
        assert result.returncode == 0
        assert 'TST-T002' in result.stdout
        assert 'subtask' in result.stdout.lower()


def test_task_create_sequential_ids():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_epic(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task 1')
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task 2')
        result = run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task 3')
        assert 'TST-T003' in result.stdout


def test_task_create_invalid_parent():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_epic(tmpdir)
        result = run_cli('--db', db, 'task', 'create',
                         '--parent', 'TST-E999', '--title', 'Bad Parent')
        assert result.returncode == 1


def test_task_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_epic(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task A')
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task B')
        result = run_cli('--db', db, 'task', 'list')
        assert 'Task A' in result.stdout
        assert 'Task B' in result.stdout


def test_task_list_filter_by_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_epic(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task A')
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task B')
        run_cli('--db', db, 'task', 'update', 'TST-T001', '--status', 'done')
        result = run_cli('--db', db, 'task', 'list', '--status', 'todo')
        assert 'Task A' not in result.stdout
        assert 'Task B' in result.stdout


def test_task_show():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_epic(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001',
                '--title', 'My Task', '--todo', '- [ ] Step 1')
        result = run_cli('--db', db, 'task', 'show', 'TST-T001')
        assert 'My Task' in result.stdout
        assert 'Step 1' in result.stdout


def test_task_show_subtask_label():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_epic(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Parent')
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-T001', '--title', 'Child')
        result = run_cli('--db', db, 'task', 'show', 'TST-T002')
        assert 'SubTask' in result.stdout


def test_task_update_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_epic(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'My Task')
        result = run_cli('--db', db, 'task', 'update', 'TST-T001', '--status', 'in_progress')
        assert result.returncode == 0

        conn = sqlite3.connect(os.path.join(pp, 'taskops.db'))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status FROM tasks WHERE id='TST-T001'").fetchone()
        assert row['status'] == 'in_progress'
        conn.close()


def test_task_update_interrupt():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_epic(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'My Task')
        run_cli('--db', db, 'task', 'update', 'TST-T001',
                '--status', 'interrupted', '--interrupt', 'Need API key')
        conn = sqlite3.connect(os.path.join(pp, 'taskops.db'))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM tasks WHERE id='TST-T001'").fetchone()
        assert row['status'] == 'interrupted'
        assert row['interrupt'] == 'Need API key'
        conn.close()


def test_task_delete():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_epic(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'My Task')
        result = run_cli('--db', db, 'task', 'delete', 'TST-T001')
        assert result.returncode == 0
        assert 'Deleted' in result.stdout


def test_task_delete_with_subtasks_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_epic(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Parent')
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-T001', '--title', 'Child')
        result = run_cli('--db', db, 'task', 'delete', 'TST-T001')
        assert result.returncode == 1
        assert 'subtask' in result.stdout.lower()
