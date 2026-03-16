"""Integration tests for init command flow.
init 커맨드 통합 테스트: DB 상태 및 파일 내용 검증.
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


def test_init_creates_db_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path = os.path.join(tmpdir, 'myproj')
        result = run_cli('init', '--name', 'MyProj', '--prefix', 'MYP', '--path', proj_path)
        assert result.returncode == 0, f"init failed: {result.stderr}"
        assert os.path.exists(os.path.join(proj_path, 'taskops.db'))


def test_init_creates_required_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path = os.path.join(tmpdir, 'myproj')
        run_cli('init', '--name', 'MyProj', '--prefix', 'MYP', '--path', proj_path)

        assert os.path.exists(os.path.join(proj_path, 'TASKOPS.md')), "TASKOPS.md not created"
        assert not os.path.exists(os.path.join(proj_path, 'AGENTS.md')), "AGENTS.md should not be created"
        assert not os.path.exists(os.path.join(proj_path, 'SETTINGS.md')), "SETTINGS.md should not be created"
        assert not os.path.isdir(os.path.join(proj_path, 'resources')), "resources/ should not be created"


def test_init_db_has_correct_tables():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path = os.path.join(tmpdir, 'myproj')
        run_cli('init', '--name', 'MyProj', '--prefix', 'MYP', '--path', proj_path)
        db_path = os.path.join(proj_path, 'taskops.db')

        conn = sqlite3.connect(db_path)
        try:
            tables = {row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            assert 'tasks' in tables
            assert 'operations' in tables
            assert 'resources' in tables
            assert 'settings' in tables
        finally:
            conn.close()


def test_init_project_record_in_db():
    """Project name/prefix stored as project-type task record."""
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path = os.path.join(tmpdir, 'myproj')
        run_cli('init', '--name', 'TestProject', '--prefix', 'TST', '--path', proj_path)
        db_path = os.path.join(proj_path, 'taskops.db')

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT id, title, type FROM tasks WHERE type='project'"
            ).fetchone()
            assert row is not None, "No project record found in tasks table"
            assert row['id'] == 'TST'
            assert row['title'] == 'TestProject'

            # Default settings should be present
            setting = conn.execute(
                "SELECT value FROM settings WHERE key='autonomy_level'"
            ).fetchone()
            assert setting is not None
        finally:
            conn.close()


def test_init_taskops_md_contains_project_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path = os.path.join(tmpdir, 'myproj')
        run_cli('init', '--name', 'TestProject', '--prefix', 'TST', '--path', proj_path)

        taskops_path = os.path.join(proj_path, 'TASKOPS.md')
        with open(taskops_path, encoding='utf-8') as f:
            content = f.read()
        assert 'TestProject' in content


def test_init_idempotent():
    """Running init twice in the same dir does not fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path = os.path.join(tmpdir, 'myproj')
        run_cli('init', '--name', 'MyProj', '--prefix', 'MYP', '--path', proj_path)
        result = run_cli('init', '--name', 'MyProj', '--prefix', 'MYP', '--path', proj_path)
        assert result.returncode == 0
