"""Unit tests for init command.
init 커맨드 유닛 테스트.
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


def test_init_creates_project_structure():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, 'my-project')
        result = run_cli('init', '--name', 'My Project', '--prefix', 'TOS', '--path', project_path)
        assert result.returncode == 0
        assert os.path.exists(os.path.join(project_path, 'taskops.db'))
        assert os.path.exists(os.path.join(project_path, 'TODO.md'))
        assert os.path.exists(os.path.join(project_path, 'AGENTS.md'))
        assert os.path.exists(os.path.join(project_path, 'SETTINGS.md'))
        assert os.path.isdir(os.path.join(project_path, 'resources'))


def test_init_creates_project_record_in_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, 'test-proj')
        run_cli('init', '--name', 'Test Project', '--prefix', 'TST', '--path', project_path)

        conn = sqlite3.connect(os.path.join(project_path, 'taskops.db'))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM tasks WHERE id='TST'").fetchone()
        assert row is not None
        assert row['type'] == 'project'
        assert row['title'] == 'Test Project'
        assert row['status'] == 'in_progress'
        conn.close()


def test_init_inserts_default_settings():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, 'test-proj')
        run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', project_path)

        conn = sqlite3.connect(os.path.join(project_path, 'taskops.db'))
        rows = conn.execute("SELECT key FROM settings").fetchall()
        keys = [r[0] for r in rows]
        assert 'autonomy_level' in keys
        assert 'commit_style' in keys
        assert 'use_subagent' in keys
        assert 'parallel_execution' in keys
        assert 'progress_interval' in keys
        conn.close()


def test_init_todo_contains_project_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, 'test-proj')
        run_cli('init', '--name', 'My Cool Project', '--prefix', 'MCP', '--path', project_path)

        with open(os.path.join(project_path, 'TODO.md'), encoding='utf-8') as f:
            content = f.read()
        assert 'My Cool Project' in content
        assert 'MCP' in content


def test_init_is_idempotent():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, 'test-proj')
        run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', project_path)
        result = run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', project_path)
        assert result.returncode == 0


def test_init_output_message():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, 'test-proj')
        result = run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', project_path)
        assert "Project 'Test' initialized" in result.stdout
        assert 'TST' in result.stdout
