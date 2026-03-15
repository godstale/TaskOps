"""Integration tests for workflow scenarios.
workflow 통합 테스트: 순차/병렬/의존성 시나리오별 next 결과 검증.
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


def setup_project(tmpdir):
    """Initialize project and return (proj_path, db_path)."""
    proj_path = os.path.join(tmpdir, 'wf-proj')
    run_cli('init', '--name', 'WFTest', '--prefix', 'WFT', '--path', proj_path)
    db = os.path.join(proj_path, 'taskops.db')
    run_cli('--db', db, 'epic', 'create', '--title', 'Epic A')
    return proj_path, db


def test_sequential_workflow_next_first_task():
    """set-order defines display order; seq_order alone does not block tasks.
    To enforce sequential execution, use add-dep in addition to set-order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        _, db = setup_project(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'WFT-E001', '--title', 'Task 1')
        run_cli('--db', db, 'task', 'create', '--parent', 'WFT-E001', '--title', 'Task 2')
        run_cli('--db', db, 'workflow', 'set-order', 'WFT-T001', 'WFT-T002')
        # Add explicit dependency to enforce sequential execution
        run_cli('--db', db, 'workflow', 'add-dep', 'WFT-T002', '--depends-on', 'WFT-T001')

        result = run_cli('--db', db, 'workflow', 'next')
        assert 'WFT-T001' in result.stdout
        assert 'WFT-T002' not in result.stdout


def test_sequential_workflow_advances_after_done():
    with tempfile.TemporaryDirectory() as tmpdir:
        _, db = setup_project(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'WFT-E001', '--title', 'Task 1')
        run_cli('--db', db, 'task', 'create', '--parent', 'WFT-E001', '--title', 'Task 2')
        run_cli('--db', db, 'workflow', 'set-order', 'WFT-T001', 'WFT-T002')

        run_cli('--db', db, 'task', 'update', 'WFT-T001', '--status', 'done')

        result = run_cli('--db', db, 'workflow', 'next')
        assert 'WFT-T002' in result.stdout


def test_parallel_workflow_returns_both_tasks():
    with tempfile.TemporaryDirectory() as tmpdir:
        _, db = setup_project(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'WFT-E001', '--title', 'Task 1')
        run_cli('--db', db, 'task', 'create', '--parent', 'WFT-E001', '--title', 'Task 2')
        run_cli('--db', db, 'workflow', 'set-parallel', '--group', 'grp-a', 'WFT-T001', 'WFT-T002')

        result = run_cli('--db', db, 'workflow', 'next')
        assert 'WFT-T001' in result.stdout
        assert 'WFT-T002' in result.stdout


def test_dependency_blocks_task_until_dep_done():
    with tempfile.TemporaryDirectory() as tmpdir:
        _, db = setup_project(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'WFT-E001', '--title', 'Task 1')
        run_cli('--db', db, 'task', 'create', '--parent', 'WFT-E001', '--title', 'Task 2')
        run_cli('--db', db, 'workflow', 'set-order', 'WFT-T001', 'WFT-T002')
        run_cli('--db', db, 'workflow', 'add-dep', 'WFT-T002', '--depends-on', 'WFT-T001')

        # T002 blocked — only T001 available
        result = run_cli('--db', db, 'workflow', 'next')
        assert 'WFT-T001' in result.stdout
        assert 'WFT-T002' not in result.stdout

        # After T001 done, T002 unblocked
        run_cli('--db', db, 'task', 'update', 'WFT-T001', '--status', 'done')
        result = run_cli('--db', db, 'workflow', 'next')
        assert 'WFT-T002' in result.stdout


def test_workflow_next_empty_when_all_done():
    with tempfile.TemporaryDirectory() as tmpdir:
        _, db = setup_project(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'WFT-E001', '--title', 'Task 1')
        run_cli('--db', db, 'workflow', 'set-order', 'WFT-T001')
        run_cli('--db', db, 'task', 'update', 'WFT-T001', '--status', 'done')

        result = run_cli('--db', db, 'workflow', 'next')
        # Should either say nothing or report no tasks
        assert 'WFT-T001' not in result.stdout
