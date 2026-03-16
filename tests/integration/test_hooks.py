"""Integration tests for hook scripts.
Hook 스크립트 통합 테스트.
"""
import os
import subprocess
import sys
import sqlite3
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}

# On Windows, prefer Git Bash over WSL bash
GIT_BASH = r'C:\Program Files\Git\usr\bin\bash.exe'
BASH = GIT_BASH if os.path.exists(GIT_BASH) else 'bash'


def run_cli(*args):
    return subprocess.run(
        [sys.executable, '-m', 'cli', *args],
        capture_output=True, encoding='utf-8', errors='replace',
        cwd=PROJECT_ROOT, env=ENV
    )


def run_hook(hook_name, *args, cwd=None):
    hook_path = os.path.join(PROJECT_ROOT, 'hooks', hook_name)
    return subprocess.run(
        [BASH, hook_path, *args],
        capture_output=True, encoding='utf-8', errors='replace',
        cwd=cwd or PROJECT_ROOT, env=ENV
    )


def setup_project_with_task(tmpdir):
    pp = os.path.join(tmpdir, 'test-proj')
    run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
    db = os.path.join(pp, 'taskops.db')
    run_cli('--db', db, 'epic', 'create', '--title', 'Epic A')
    run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task 1')
    run_cli('--db', db, 'workflow', 'set-order', 'TST-T001')
    return pp, db


def test_on_task_start_updates_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        result = run_hook('on_task_start.sh', 'TST-T001', cwd=pp)

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute("SELECT status FROM tasks WHERE id='TST-T001'").fetchone()
            assert row['status'] == 'in_progress', f"Expected in_progress, got {row['status']}. Hook stderr: {result.stderr}"

            op = conn.execute(
                "SELECT operation_type FROM operations WHERE task_id='TST-T001'"
            ).fetchone()
            assert op['operation_type'] == 'start'
        finally:
            conn.close()


def test_on_task_start_empty_id_no_error():
    result = run_hook('on_task_start.sh')
    assert result.returncode == 0


def test_on_task_complete_updates_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        run_cli('--db', db, 'task', 'update', 'TST-T001', '--status', 'in_progress')
        result = run_hook('on_task_complete.sh', 'TST-T001', cwd=pp)

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute("SELECT status FROM tasks WHERE id='TST-T001'").fetchone()
            assert row['status'] == 'done', f"Expected done, got {row['status']}. Hook stderr: {result.stderr}"

            op = conn.execute(
                "SELECT operation_type FROM operations WHERE task_id='TST-T001' AND operation_type='complete'"
            ).fetchone()
            assert op is not None
        finally:
            conn.close()


def test_on_task_complete_no_todo_md_written():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        # Remove any TODO.md created by init, then verify hook does not recreate it
        todo_path = os.path.join(pp, 'TODO.md')
        if os.path.exists(todo_path):
            os.remove(todo_path)
        run_hook('on_task_complete.sh', 'TST-T001', cwd=pp)
        assert not os.path.exists(todo_path)


def test_on_tool_use_records_progress():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        run_cli('--db', db, 'task', 'update', 'TST-T001', '--status', 'in_progress')
        result = run_hook('on_tool_use.sh', cwd=pp)

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        try:
            op = conn.execute(
                "SELECT * FROM operations WHERE task_id='TST-T001' AND operation_type='progress'"
            ).fetchone()
            assert op is not None, f"No progress op found. Hook stderr: {result.stderr}"
            assert 'Tool used' in op['summary']
        finally:
            conn.close()
