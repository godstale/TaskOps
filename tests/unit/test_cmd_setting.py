"""Unit tests for setting command.
setting 커맨드 유닛 테스트.
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


def setup_project(tmpdir):
    pp = os.path.join(tmpdir, 'test-proj')
    run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
    return pp, os.path.join(pp, 'taskops.db')


def test_setting_set():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'setting', 'set', 'my_key', 'my_value',
                         '--desc', 'My description')
        assert result.returncode == 0
        assert 'my_key' in result.stdout
        assert 'my_value' in result.stdout


def test_setting_set_updates_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        run_cli('--db', db, 'setting', 'set', 'my_key', 'val1')

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT value FROM settings WHERE key='my_key'").fetchone()
        assert row['value'] == 'val1'
        conn.close()


def test_setting_set_upsert():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        run_cli('--db', db, 'setting', 'set', 'my_key', 'val1')
        run_cli('--db', db, 'setting', 'set', 'my_key', 'val2')

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT value FROM settings WHERE key='my_key'").fetchone()
        assert row['value'] == 'val2'
        conn.close()


def test_setting_set_regenerates_settings_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        run_cli('--db', db, 'setting', 'set', 'custom_key', 'custom_val',
                '--desc', 'Custom setting')

        with open(os.path.join(pp, 'SETTINGS.md'), encoding='utf-8') as f:
            content = f.read()
        assert 'custom_key' in content
        assert 'custom_val' in content


def test_setting_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'setting', 'get', 'autonomy_level')
        assert result.returncode == 0
        assert 'moderate' in result.stdout


def test_setting_get_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'setting', 'get', 'nonexistent')
        assert result.returncode == 1


def test_setting_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'setting', 'list')
        assert result.returncode == 0
        assert 'autonomy_level' in result.stdout
        assert 'commit_style' in result.stdout
        assert 'use_subagent' in result.stdout


def test_setting_delete():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'setting', 'delete', 'autonomy_level')
        assert result.returncode == 0
        assert 'deleted' in result.stdout.lower()

        conn = sqlite3.connect(db)
        row = conn.execute("SELECT * FROM settings WHERE key='autonomy_level'").fetchone()
        assert row is None
        conn.close()


def test_setting_delete_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        result = run_cli('--db', db, 'setting', 'delete', 'nonexistent')
        assert result.returncode == 1


def test_setting_delete_regenerates_settings_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        pp, db = setup_project(tmpdir)
        run_cli('--db', db, 'setting', 'delete', 'autonomy_level')

        with open(os.path.join(pp, 'SETTINGS.md'), encoding='utf-8') as f:
            content = f.read()
        assert 'autonomy_level' not in content
