"""Unit tests for workflow command.
workflow 커맨드 유닛 테스트.
"""
import os
import subprocess
import sys
import sqlite3
import json
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}


def run_cli(*args):
    return subprocess.run(
        [sys.executable, '-m', 'cli', *args],
        capture_output=True, encoding='utf-8', errors='replace',
        cwd=PROJECT_ROOT, env=ENV
    )


def setup_project_with_tasks(tmpdir):
    """Init project, create epic, create 3 tasks."""
    pp = os.path.join(tmpdir, 'test-proj')
    run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
    db = os.path.join(pp, 'taskops.db')
    run_cli('--db', db, 'epic', 'create', '--title', 'Epic A')
    run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task 1')
    run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task 2')
    run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task 3')
    return pp, db


def test_workflow_set_order():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        result = run_cli('--db', db, 'workflow', 'set-order',
                         'TST-T001', 'TST-T002', 'TST-T003')
        assert result.returncode == 0
        assert '1. TST-T001' in result.stdout
        assert '2. TST-T002' in result.stdout
        assert '3. TST-T003' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        r1 = conn.execute("SELECT seq_order FROM tasks WHERE id='TST-T001'").fetchone()
        r2 = conn.execute("SELECT seq_order FROM tasks WHERE id='TST-T002'").fetchone()
        r3 = conn.execute("SELECT seq_order FROM tasks WHERE id='TST-T003'").fetchone()
        assert r1['seq_order'] == 1
        assert r2['seq_order'] == 2
        assert r3['seq_order'] == 3
        conn.close()


def test_workflow_set_order_invalid_task():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        result = run_cli('--db', db, 'workflow', 'set-order', 'TST-T999')
        assert result.returncode == 1


def test_workflow_set_parallel():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        result = run_cli('--db', db, 'workflow', 'set-parallel',
                         '--group', 'auth-group', 'TST-T002', 'TST-T003')
        assert result.returncode == 0
        assert 'auth-group' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        r2 = conn.execute("SELECT parallel_group FROM tasks WHERE id='TST-T002'").fetchone()
        r3 = conn.execute("SELECT parallel_group FROM tasks WHERE id='TST-T003'").fetchone()
        assert r2['parallel_group'] == 'auth-group'
        assert r3['parallel_group'] == 'auth-group'
        conn.close()


def test_workflow_add_dep():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        result = run_cli('--db', db, 'workflow', 'add-dep', 'TST-T003',
                         '--depends-on', 'TST-T001', 'TST-T002')
        assert result.returncode == 0
        assert 'TST-T001' in result.stdout
        assert 'TST-T002' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT depends_on FROM tasks WHERE id='TST-T003'").fetchone()
        deps = json.loads(row['depends_on'])
        assert 'TST-T001' in deps
        assert 'TST-T002' in deps
        conn.close()


def test_workflow_add_dep_merges():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'workflow', 'add-dep', 'TST-T003',
                '--depends-on', 'TST-T001')
        run_cli('--db', db, 'workflow', 'add-dep', 'TST-T003',
                '--depends-on', 'TST-T002')

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT depends_on FROM tasks WHERE id='TST-T003'").fetchone()
        deps = json.loads(row['depends_on'])
        assert len(deps) == 2
        conn.close()


def test_workflow_add_dep_no_duplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'workflow', 'add-dep', 'TST-T003', '--depends-on', 'TST-T001')
        run_cli('--db', db, 'workflow', 'add-dep', 'TST-T003', '--depends-on', 'TST-T001')

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT depends_on FROM tasks WHERE id='TST-T003'").fetchone()
        deps = json.loads(row['depends_on'])
        assert deps.count('TST-T001') == 1
        conn.close()


def test_workflow_show():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'workflow', 'set-order', 'TST-T001', 'TST-T002', 'TST-T003')
        run_cli('--db', db, 'workflow', 'set-parallel', '--group', 'grp', 'TST-T002', 'TST-T003')
        result = run_cli('--db', db, 'workflow', 'show')
        assert result.returncode == 0
        assert 'TST-T001' in result.stdout
        assert 'TST-T002' in result.stdout
        assert 'grp' in result.stdout


def test_workflow_show_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        result = run_cli('--db', db, 'workflow', 'show')
        assert 'No workflow' in result.stdout


def test_workflow_next_all_todo():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'workflow', 'set-order', 'TST-T001', 'TST-T002', 'TST-T003')
        result = run_cli('--db', db, 'workflow', 'next')
        assert 'TST-T001' in result.stdout


def test_workflow_next_respects_dependencies():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'workflow', 'set-order', 'TST-T001', 'TST-T002', 'TST-T003')
        run_cli('--db', db, 'workflow', 'add-dep', 'TST-T002', '--depends-on', 'TST-T001')
        run_cli('--db', db, 'workflow', 'add-dep', 'TST-T003', '--depends-on', 'TST-T002')

        result = run_cli('--db', db, 'workflow', 'next')
        assert 'TST-T001' in result.stdout
        assert 'TST-T002' not in result.stdout
        assert 'TST-T003' not in result.stdout


def test_workflow_next_after_dep_done():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'workflow', 'set-order', 'TST-T001', 'TST-T002', 'TST-T003')
        run_cli('--db', db, 'workflow', 'add-dep', 'TST-T002', '--depends-on', 'TST-T001')
        run_cli('--db', db, 'task', 'update', 'TST-T001', '--status', 'done')

        result = run_cli('--db', db, 'workflow', 'next')
        assert 'TST-T002' in result.stdout


def test_workflow_current_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        result = run_cli('--db', db, 'workflow', 'current')
        assert result.returncode == 0
        assert result.stdout.strip() == ''


def test_workflow_current_active():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'task', 'update', 'TST-T001', '--status', 'in_progress')
        result = run_cli('--db', db, 'workflow', 'current')
        assert result.stdout.strip() == 'TST-T001'
