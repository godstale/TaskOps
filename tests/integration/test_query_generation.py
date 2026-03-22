"""Integration tests for query generation.
query 생성 통합 테스트: show 결과 포맷 검증.
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
    proj_path = os.path.join(tmpdir, 'qry-proj')
    run_cli('init', '--name', 'QryTest', '--prefix', 'QRY', '--path', proj_path)
    db = os.path.join(proj_path, 'taskops.db')
    run_cli('--db', db, 'workflow', 'create', '--title', 'QRY Plan')  # → QRY-W001
    run_cli('--db', db, 'epic', 'create', '--workflow', 'QRY-W001', '--title', 'Epic A')
    run_cli('--db', db, 'task', 'create', '--workflow', 'QRY-W001', '--parent', 'QRY-E001', '--title', 'Task One')
    run_cli('--db', db, 'task', 'create', '--workflow', 'QRY-W001', '--parent', 'QRY-E001', '--title', 'Task Two')
    run_cli('--db', db, 'workflow', 'set-order', 'QRY-T001', 'QRY-T002')
    return proj_path, db


def test_show_no_file_created():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path, db = setup_project(tmpdir)
        # Remove any TODO.md created by init, then verify query show does not recreate it
        todo_path = os.path.join(proj_path, 'TODO.md')
        if os.path.exists(todo_path):
            os.remove(todo_path)
        result = run_cli('--db', db, 'query', 'show')
        assert result.returncode == 0
        assert not os.path.exists(todo_path)


def test_show_contains_task_titles():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'query', 'show')
        content = result.stdout
        assert 'Task One' in content
        assert 'Task Two' in content


def test_show_reflects_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path, db = setup_project(tmpdir)
        run_cli('--db', db, 'task', 'update', 'QRY-T001', '--status', 'done')
        result = run_cli('--db', db, 'query', 'show')
        content = result.stdout
        assert 'done' in content
