"""Integration tests for query generation.
query 생성 통합 테스트: generate-todo/generate-ops 결과 포맷 검증.
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
    run_cli('--db', db, 'epic', 'create', '--title', 'Epic A')
    run_cli('--db', db, 'task', 'create', '--parent', 'QRY-E001', '--title', 'Task One')
    run_cli('--db', db, 'task', 'create', '--parent', 'QRY-E001', '--title', 'Task Two')
    run_cli('--db', db, 'workflow', 'set-order', 'QRY-T001', 'QRY-T002')
    return proj_path, db


def test_generate_todo_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path, db = setup_project(tmpdir)
        os.remove(os.path.join(proj_path, 'TODO.md'))  # remove init-created file
        result = run_cli('--db', db, 'query', 'generate-todo')
        assert result.returncode == 0
        assert os.path.exists(os.path.join(proj_path, 'TODO.md'))


def test_generate_todo_contains_task_titles():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path, db = setup_project(tmpdir)
        run_cli('--db', db, 'query', 'generate-todo')

        with open(os.path.join(proj_path, 'TODO.md'), encoding='utf-8') as f:
            content = f.read()
        assert 'Task One' in content
        assert 'Task Two' in content


def test_generate_todo_reflects_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path, db = setup_project(tmpdir)
        run_cli('--db', db, 'task', 'update', 'QRY-T001', '--status', 'done')
        run_cli('--db', db, 'query', 'generate-todo')

        with open(os.path.join(proj_path, 'TODO.md'), encoding='utf-8') as f:
            content = f.read()
        assert '`done`' in content


def test_generate_ops_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path, db = setup_project(tmpdir)
        run_cli('--db', db, 'op', 'start', 'QRY-T001', '--platform', 'claude_code')
        result = run_cli('--db', db, 'query', 'generate-ops')
        assert result.returncode == 0
        assert os.path.exists(os.path.join(proj_path, 'TASK_OPERATIONS.md'))


def test_generate_ops_contains_operation_records():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path, db = setup_project(tmpdir)
        run_cli('--db', db, 'op', 'start', 'QRY-T001', '--platform', 'claude_code')
        run_cli('--db', db, 'op', 'progress', 'QRY-T001', '--summary', 'Halfway done')
        run_cli('--db', db, 'query', 'generate-ops')

        with open(os.path.join(proj_path, 'TASK_OPERATIONS.md'), encoding='utf-8') as f:
            content = f.read()
        assert 'start' in content
        assert 'Halfway done' in content
