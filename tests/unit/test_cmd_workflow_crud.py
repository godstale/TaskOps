"""Unit tests for workflow create/list/delete commands.
workflow create/list/delete 커맨드 유닛 테스트.
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
    pp = os.path.join(tmpdir, 'proj')
    run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
    return pp, os.path.join(pp, 'taskops.db')


def test_workflow_create_returns_id():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_project(d)
        r = run_cli('--db', db, 'workflow', 'create', '--title', 'My Todo List')
        assert r.returncode == 0
        assert 'TST-W001' in r.stdout


def test_workflow_create_sequential_ids():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_project(d)
        run_cli('--db', db, 'workflow', 'create', '--title', 'First')
        r = run_cli('--db', db, 'workflow', 'create', '--title', 'Second')
        assert r.returncode == 0
        assert 'TST-W002' in r.stdout


def test_workflow_create_with_source_file():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_project(d)
        r = run_cli('--db', db, 'workflow', 'create', '--title', 'With Source',
                    '--source-file', 'plan.md')
        assert r.returncode == 0
        assert 'TST-W001' in r.stdout


def test_workflow_list_shows_all():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_project(d)
        run_cli('--db', db, 'workflow', 'create', '--title', 'Alpha')
        run_cli('--db', db, 'workflow', 'create', '--title', 'Beta')
        r = run_cli('--db', db, 'workflow', 'list')
        assert r.returncode == 0
        assert 'Alpha' in r.stdout
        assert 'Beta' in r.stdout


def test_workflow_list_empty():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_project(d)
        r = run_cli('--db', db, 'workflow', 'list')
        assert r.returncode == 0
        assert 'No workflows' in r.stdout


def test_workflow_delete_removes_workflow():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_project(d)
        run_cli('--db', db, 'workflow', 'create', '--title', 'Temp')
        r = run_cli('--db', db, 'workflow', 'delete', 'TST-W001')
        assert r.returncode == 0
        listed = run_cli('--db', db, 'workflow', 'list')
        assert 'Temp' not in listed.stdout


def test_workflow_delete_nonexistent_fails():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_project(d)
        r = run_cli('--db', db, 'workflow', 'delete', 'TST-W999')
        assert r.returncode != 0


def test_workflow_list_shows_source_file():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_project(d)
        run_cli('--db', db, 'workflow', 'create', '--title', 'Sourced',
                '--source-file', 'todo.md')
        r = run_cli('--db', db, 'workflow', 'list')
        assert 'todo.md' in r.stdout
