"""Unit tests for workflow export command."""
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


def setup_workflow(tmpdir):
    """Create project + workflow with 2 epics, tasks, and a subtask."""
    pp = os.path.join(tmpdir, 'proj')
    db = os.path.join(pp, 'taskops.db')
    run_cli('init', '--name', 'Test Project', '--prefix', 'TST', '--path', pp)
    run_cli('--db', db, 'workflow', 'create', '--title', 'My Plan')
    structure = (
        '{"epics":['
        '{"title":"Auth","tasks":['
        '{"title":"Login API"},'
        '{"title":"JWT","tasks":[{"title":"Token generation"}]}'
        ']},'
        '{"title":"Database","tasks":[{"title":"Schema design"}]}'
        ']}'
    )
    run_cli('--db', db, 'workflow', 'import', 'TST-W001', '--structure', structure)
    return pp, db


def test_workflow_export_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_workflow(tmpdir)
        out = os.path.join(pp, 'MY_TODO.md')
        result = run_cli('--db', db, 'workflow', 'export', 'TST-W001', '--output', out)
        assert result.returncode == 0
        assert os.path.exists(out)


def test_workflow_export_default_output_next_to_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_workflow(tmpdir)
        result = run_cli('--db', db, 'workflow', 'export', 'TST-W001')
        assert result.returncode == 0
        assert os.path.exists(os.path.join(pp, 'TODO.md'))


def test_workflow_export_contains_epics_and_tasks():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_workflow(tmpdir)
        out = os.path.join(pp, 'TODO.md')
        run_cli('--db', db, 'workflow', 'export', 'TST-W001', '--output', out)
        with open(out, encoding='utf-8') as f:
            content = f.read()
        assert 'Auth' in content
        assert 'Login API' in content
        assert 'JWT' in content
        assert 'Token generation' in content
        assert 'Database' in content
        assert 'Schema design' in content


def test_workflow_export_done_task_marked():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_workflow(tmpdir)
        run_cli('--db', db, 'task', 'update', 'TST-T001', '--status', 'done')
        out = os.path.join(pp, 'TODO.md')
        run_cli('--db', db, 'workflow', 'export', 'TST-W001', '--output', out)
        with open(out, encoding='utf-8') as f:
            content = f.read()
        assert '[x]' in content


def test_workflow_export_todo_task_unchecked():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_workflow(tmpdir)
        out = os.path.join(pp, 'TODO.md')
        run_cli('--db', db, 'workflow', 'export', 'TST-W001', '--output', out)
        with open(out, encoding='utf-8') as f:
            content = f.read()
        assert '[ ]' in content


def test_workflow_export_invalid_workflow_id():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_workflow(tmpdir)
        result = run_cli('--db', db, 'workflow', 'export', 'TST-W999')
        assert result.returncode == 1


def test_workflow_export_prints_output_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_workflow(tmpdir)
        out = os.path.join(pp, 'OUT.md')
        result = run_cli('--db', db, 'workflow', 'export', 'TST-W001', '--output', out)
        assert result.returncode == 0
        assert 'TST-W001' in result.stdout
