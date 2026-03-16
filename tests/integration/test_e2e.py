"""End-to-end integration test: full project lifecycle.
전체 라이프사이클 통합 테스트: init → epic → task → subtask → objective → workflow → op → query.
"""
import os
import subprocess
import sys
import sqlite3
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}


def cli(*args):
    result = subprocess.run(
        [sys.executable, '-m', 'cli', *args],
        capture_output=True, encoding='utf-8', errors='replace',
        cwd=PROJECT_ROOT, env=ENV
    )
    return result


def test_full_project_lifecycle():
    """
    Full lifecycle: init → epic → tasks → subtask → objective
                  → workflow → op recording → query status → generate reports
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        proj = os.path.join(tmpdir, 'e2e-proj')

        # --- Phase 1: Init ---
        r = cli('init', '--name', 'E2EProject', '--prefix', 'E2E', '--path', proj)
        assert r.returncode == 0, f"init failed: {r.stderr}"
        db = os.path.join(proj, 'taskops.db')
        assert os.path.exists(db)
        assert os.path.exists(os.path.join(proj, 'TODO.md'))

        # --- Phase 2: Planning ---
        # Create Epic
        r = cli('--db', db, 'epic', 'create', '--title', 'Core Feature')
        assert r.returncode == 0

        # Create Tasks under Epic
        r = cli('--db', db, 'task', 'create', '--parent', 'E2E-E001', '--title', 'Design API')
        assert r.returncode == 0
        r = cli('--db', db, 'task', 'create', '--parent', 'E2E-E001', '--title', 'Implement API')
        assert r.returncode == 0
        r = cli('--db', db, 'task', 'create', '--parent', 'E2E-E001', '--title', 'Write Tests')
        assert r.returncode == 0

        # Create SubTask under Task
        r = cli('--db', db, 'task', 'create', '--parent', 'E2E-T002', '--title', 'JWT Auth')
        assert r.returncode == 0

        # Create Objective
        r = cli('--db', db, 'objective', 'create', '--title', 'MVP Done', '--milestone', 'Core features complete')
        assert r.returncode == 0

        # --- Phase 3: Workflow Setup ---
        r = cli('--db', db, 'workflow', 'set-order', 'E2E-T001', 'E2E-T002', 'E2E-T003')
        assert r.returncode == 0
        r = cli('--db', db, 'workflow', 'add-dep', 'E2E-T002', '--depends-on', 'E2E-T001')
        assert r.returncode == 0
        r = cli('--db', db, 'workflow', 'add-dep', 'E2E-T003', '--depends-on', 'E2E-T002')
        assert r.returncode == 0

        # Show initial task structure
        r = cli('--db', db, 'query', 'show')
        assert r.returncode == 0

        # --- Phase 4: Execute Task 1 ---
        # Check next
        r = cli('--db', db, 'workflow', 'next')
        assert 'E2E-T001' in r.stdout

        # Start task
        r = cli('--db', db, 'task', 'update', 'E2E-T001', '--status', 'in_progress')
        assert r.returncode == 0
        r = cli('--db', db, 'op', 'start', 'E2E-T001', '--platform', 'claude_code')
        assert r.returncode == 0

        # Record progress
        r = cli('--db', db, 'op', 'progress', 'E2E-T001', '--summary', 'API schema defined')
        assert r.returncode == 0

        # Complete task
        r = cli('--db', db, 'task', 'update', 'E2E-T001', '--status', 'done')
        assert r.returncode == 0
        r = cli('--db', db, 'op', 'complete', 'E2E-T001', '--summary', 'Design done')
        assert r.returncode == 0

        # --- Phase 5: Execute Task 2 (dependency check) ---
        r = cli('--db', db, 'workflow', 'next')
        assert 'E2E-T002' in r.stdout

        r = cli('--db', db, 'task', 'update', 'E2E-T002', '--status', 'in_progress')
        r = cli('--db', db, 'op', 'start', 'E2E-T002', '--platform', 'claude_code')
        r = cli('--db', db, 'task', 'update', 'E2E-T002', '--status', 'done')
        r = cli('--db', db, 'op', 'complete', 'E2E-T002', '--summary', 'Implementation done')
        assert r.returncode == 0

        # --- Phase 6: Add resource ---
        r = cli('--db', db, 'resource', 'add', 'E2E-T002',
                '--path', './docs/spec.md', '--type', 'output', '--desc', 'API spec')
        assert r.returncode == 0

        # --- Phase 7: Settings ---
        r = cli('--db', db, 'setting', 'set', 'review_required', 'true', '--desc', 'Requires code review')
        assert r.returncode == 0
        r = cli('--db', db, 'setting', 'get', 'review_required')
        assert 'true' in r.stdout

        # --- Phase 8: Query and Reports ---
        r = cli('--db', db, 'query', 'status')
        assert r.returncode == 0
        assert 'E2E' in r.stdout or 'done' in r.stdout

        r = cli('--db', db, 'query', 'show')
        assert r.returncode == 0
        assert 'done' in r.stdout

        # --- Phase 9: DB state verification ---
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        try:
            done_count = conn.execute(
                "SELECT COUNT(*) as c FROM tasks WHERE status='done'"
            ).fetchone()['c']
            assert done_count == 2  # T001 and T002

            op_count = conn.execute(
                "SELECT COUNT(*) as c FROM operations"
            ).fetchone()['c']
            assert op_count >= 5  # start + progress + complete for T001, start + complete for T002

            resource = conn.execute(
                "SELECT * FROM resources WHERE task_id='E2E-T002'"
            ).fetchone()
            assert resource is not None

            setting = conn.execute(
                "SELECT value FROM settings WHERE key='review_required'"
            ).fetchone()
            assert setting['value'] == 'true'
        finally:
            conn.close()
