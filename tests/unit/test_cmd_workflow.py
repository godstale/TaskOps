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


def test_generate_workflow_short_basic():
    import sys
    sys.path.insert(0, PROJECT_ROOT)
    from cli.commands.utils import generate_workflow_short
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE workflows (id TEXT PRIMARY KEY)")
        assert generate_workflow_short("Real Time Sync", conn) == "RTS"
        assert generate_workflow_short("API Server Refactor", conn) == "ASR"
        assert generate_workflow_short("Build and Deploy Pipeline", conn) == "BDP"
        assert generate_workflow_short("Go", conn) == "GW"
        conn.close()
    finally:
        os.unlink(db_path)


def test_generate_workflow_short_collision():
    import sys
    sys.path.insert(0, PROJECT_ROOT)
    from cli.commands.utils import generate_workflow_short
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE workflows (id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO workflows VALUES ('PRJ-RTS')")
        conn.commit()
        result = generate_workflow_short("Real Time Sync", conn)
        assert result == "RTS1"
        conn.close()
    finally:
        os.unlink(db_path)


def test_get_workflow_prefix():
    import sys
    sys.path.insert(0, PROJECT_ROOT)
    from cli.commands.utils import get_workflow_prefix
    assert get_workflow_prefix("SMR-RTS") == "RTS"
    assert get_workflow_prefix("SMR-RTS1") == "RTS1"
    assert get_workflow_prefix("PRJ-TW") == "TW"
    assert get_workflow_prefix("PRJ-W001") == "W001"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, '-m', 'cli', *args],
        capture_output=True, encoding='utf-8', errors='replace',
        cwd=PROJECT_ROOT, env=ENV
    )


def setup_project_with_tasks(tmpdir):
    """Init project, create workflow, epic, and 3 tasks."""
    pp = os.path.join(tmpdir, 'test-proj')
    run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
    db = os.path.join(pp, 'taskops.db')
    run_cli('--db', db, 'workflow', 'create', '--title', 'Test Workflow',
            '--description', 'Test workflow for unit tests')
    run_cli('--db', db, 'epic', 'create', '--title', 'Epic A', '--workflow', 'TST-TW')
    run_cli('--db', db, 'task', 'create', '--parent', 'TW-E001', '--title', 'Task 1', '--workflow', 'TST-TW')
    run_cli('--db', db, 'task', 'create', '--parent', 'TW-E001', '--title', 'Task 2', '--workflow', 'TST-TW')
    run_cli('--db', db, 'task', 'create', '--parent', 'TW-E001', '--title', 'Task 3', '--workflow', 'TST-TW')
    return pp, db


def test_workflow_set_order():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        result = run_cli('--db', db, 'workflow', 'set-order',
                         'TW-T001', 'TW-T002', 'TW-T003')
        assert result.returncode == 0
        assert '1. TW-T001' in result.stdout
        assert '2. TW-T002' in result.stdout
        assert '3. TW-T003' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        r1 = conn.execute("SELECT seq_order FROM tasks WHERE id='TW-T001'").fetchone()
        r2 = conn.execute("SELECT seq_order FROM tasks WHERE id='TW-T002'").fetchone()
        r3 = conn.execute("SELECT seq_order FROM tasks WHERE id='TW-T003'").fetchone()
        assert r1['seq_order'] == 1
        assert r2['seq_order'] == 2
        assert r3['seq_order'] == 3
        conn.close()


def test_workflow_set_order_invalid_task():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        result = run_cli('--db', db, 'workflow', 'set-order', 'TW-T999')
        assert result.returncode == 1


def test_workflow_set_parallel():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        result = run_cli('--db', db, 'workflow', 'set-parallel',
                         '--group', 'auth-group', 'TW-T002', 'TW-T003')
        assert result.returncode == 0
        assert 'auth-group' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        r2 = conn.execute("SELECT parallel_group FROM tasks WHERE id='TW-T002'").fetchone()
        r3 = conn.execute("SELECT parallel_group FROM tasks WHERE id='TW-T003'").fetchone()
        assert r2['parallel_group'] == 'auth-group'
        assert r3['parallel_group'] == 'auth-group'
        conn.close()


def test_workflow_add_dep():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        result = run_cli('--db', db, 'workflow', 'add-dep', 'TW-T003',
                         '--depends-on', 'TW-T001', 'TW-T002')
        assert result.returncode == 0
        assert 'TW-T001' in result.stdout
        assert 'TW-T002' in result.stdout

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT depends_on FROM tasks WHERE id='TW-T003'").fetchone()
        deps = json.loads(row['depends_on'])
        assert 'TW-T001' in deps
        assert 'TW-T002' in deps
        conn.close()


def test_workflow_add_dep_merges():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'workflow', 'add-dep', 'TW-T003',
                '--depends-on', 'TW-T001')
        run_cli('--db', db, 'workflow', 'add-dep', 'TW-T003',
                '--depends-on', 'TW-T002')

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT depends_on FROM tasks WHERE id='TW-T003'").fetchone()
        deps = json.loads(row['depends_on'])
        assert len(deps) == 2
        conn.close()


def test_workflow_add_dep_no_duplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'workflow', 'add-dep', 'TW-T003', '--depends-on', 'TW-T001')
        run_cli('--db', db, 'workflow', 'add-dep', 'TW-T003', '--depends-on', 'TW-T001')

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT depends_on FROM tasks WHERE id='TW-T003'").fetchone()
        deps = json.loads(row['depends_on'])
        assert deps.count('TW-T001') == 1
        conn.close()


def test_workflow_show():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'workflow', 'set-order', 'TW-T001', 'TW-T002', 'TW-T003')
        run_cli('--db', db, 'workflow', 'set-parallel', '--group', 'grp', 'TW-T002', 'TW-T003')
        result = run_cli('--db', db, 'workflow', 'show')
        assert result.returncode == 0
        assert 'TW-T001' in result.stdout
        assert 'TW-T002' in result.stdout
        assert 'grp' in result.stdout


def test_workflow_show_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        result = run_cli('--db', db, 'workflow', 'show')
        assert 'No workflow' in result.stdout


def test_workflow_next_all_todo():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'workflow', 'set-order', 'TW-T001', 'TW-T002', 'TW-T003')
        result = run_cli('--db', db, 'workflow', 'next')
        assert 'TW-T001' in result.stdout


def test_workflow_next_respects_dependencies():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'workflow', 'set-order', 'TW-T001', 'TW-T002', 'TW-T003')
        run_cli('--db', db, 'workflow', 'add-dep', 'TW-T002', '--depends-on', 'TW-T001')
        run_cli('--db', db, 'workflow', 'add-dep', 'TW-T003', '--depends-on', 'TW-T002')

        result = run_cli('--db', db, 'workflow', 'next')
        assert 'TW-T001' in result.stdout
        assert 'TW-T002' not in result.stdout
        assert 'TW-T003' not in result.stdout


def test_workflow_next_after_dep_done():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'workflow', 'set-order', 'TW-T001', 'TW-T002', 'TW-T003')
        run_cli('--db', db, 'workflow', 'add-dep', 'TW-T002', '--depends-on', 'TW-T001')
        run_cli('--db', db, 'task', 'update', 'TW-T001', '--status', 'done')

        result = run_cli('--db', db, 'workflow', 'next')
        assert 'TW-T002' in result.stdout


def test_workflow_current_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        result = run_cli('--db', db, 'workflow', 'current')
        assert result.returncode == 0
        assert result.stdout.strip() == ''


def test_workflow_current_active():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_tasks(tmpdir)
        run_cli('--db', db, 'task', 'update', 'TW-T001', '--status', 'in_progress')
        result = run_cli('--db', db, 'workflow', 'current')
        assert result.stdout.strip() == 'TW-T001'


def test_workflow_create_with_description():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp = os.path.join(tmpdir, 'test-proj')
        run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
        db = os.path.join(pp, 'taskops.db')
        result = run_cli('--db', db, 'workflow', 'create',
                         '--title', 'Real Time Sync',
                         '--description', 'Sync engine for live data')
        assert result.returncode == 0
        assert 'TST-RTS' in result.stdout


def test_workflow_list_shows_description():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp = os.path.join(tmpdir, 'test-proj')
        run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
        db = os.path.join(pp, 'taskops.db')
        run_cli('--db', db, 'workflow', 'create',
                '--title', 'Real Time Sync',
                '--description', 'Sync engine for live data')
        result = run_cli('--db', db, 'workflow', 'list')
        assert result.returncode == 0
        assert 'TST-RTS' in result.stdout
        assert 'Sync engine for live data' in result.stdout


def test_workflow_short_id_collision():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp = os.path.join(tmpdir, 'test-proj')
        run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
        db = os.path.join(pp, 'taskops.db')
        r1 = run_cli('--db', db, 'workflow', 'create', '--title', 'Real Time Sync')
        r2 = run_cli('--db', db, 'workflow', 'create', '--title', 'Real Time Sync')
        assert r1.returncode == 0
        assert r2.returncode == 0
        assert 'TST-RTS' in r1.stdout
        assert 'TST-RTS1' in r2.stdout


def test_workflow_import_uses_wf_short_prefix():
    """Imported epics/tasks use workflow short prefix, not project prefix."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pp = os.path.join(tmpdir, 'test-proj')
        run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
        db = os.path.join(pp, 'taskops.db')
        run_cli('--db', db, 'workflow', 'create', '--title', 'Real Time Sync')
        structure = json.dumps({
            "epics": [{"title": "Epic One", "tasks": [{"title": "Task A"}]}]
        })
        result = run_cli('--db', db, 'workflow', 'import', 'TST-RTS', '--structure', structure)
        assert result.returncode == 0
        assert 'RTS-E001' in result.stdout
        assert 'RTS-T001' in result.stdout
