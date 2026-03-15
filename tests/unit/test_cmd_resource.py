"""Unit tests for resource command.
resource 커맨드 유닛 테스트.
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


def test_resource_add():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        result = run_cli('--db', db, 'resource', 'add', 'TST-T001',
                         '--path', './docs/spec.md', '--type', 'input', '--desc', 'API spec')
        assert result.returncode == 0
        assert 'spec.md' in result.stdout
        assert 'input' in result.stdout


def test_resource_add_default_type():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        result = run_cli('--db', db, 'resource', 'add', 'TST-T001',
                         '--path', './readme.md')
        assert result.returncode == 0
        assert 'reference' in result.stdout


def test_resource_add_invalid_task():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        result = run_cli('--db', db, 'resource', 'add', 'TST-T999',
                         '--path', './file.md')
        assert result.returncode == 1


def test_resource_list_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        run_cli('--db', db, 'resource', 'add', 'TST-T001',
                '--path', './a.md', '--type', 'input')
        run_cli('--db', db, 'resource', 'add', 'TST-T001',
                '--path', './b.md', '--type', 'output')
        result = run_cli('--db', db, 'resource', 'list')
        assert 'a.md' in result.stdout
        assert 'b.md' in result.stdout


def test_resource_list_filter_by_task():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        run_cli('--db', db, 'task', 'create', '--parent', 'TST-E001', '--title', 'Task 2')
        run_cli('--db', db, 'resource', 'add', 'TST-T001', '--path', './a.md')
        run_cli('--db', db, 'resource', 'add', 'TST-T002', '--path', './b.md')
        result = run_cli('--db', db, 'resource', 'list', '--task', 'TST-T001')
        assert 'a.md' in result.stdout
        assert 'b.md' not in result.stdout


def test_resource_list_filter_by_type():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        run_cli('--db', db, 'resource', 'add', 'TST-T001',
                '--path', './a.md', '--type', 'input')
        run_cli('--db', db, 'resource', 'add', 'TST-T001',
                '--path', './b.md', '--type', 'output')
        result = run_cli('--db', db, 'resource', 'list', '--type', 'input')
        assert 'a.md' in result.stdout
        assert 'b.md' not in result.stdout


def test_resource_list_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        result = run_cli('--db', db, 'resource', 'list')
        assert 'No resources' in result.stdout


def test_resource_add_all_types():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project_with_task(tmpdir)
        for t in ['input', 'output', 'reference', 'intermediate']:
            result = run_cli('--db', db, 'resource', 'add', 'TST-T001',
                             '--path', f'./{t}.md', '--type', t)
            assert result.returncode == 0

        conn = sqlite3.connect(db)
        count = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
        assert count == 4
        conn.close()
