"""Unit tests for CLI entry point.
CLI 진입점 유닛 테스트.
"""
import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}


def run_cli(*args):
    return subprocess.run(
        [sys.executable, '-m', 'cli', *args],
        capture_output=True, encoding='utf-8', errors='replace',
        cwd=PROJECT_ROOT, env=ENV
    )


def test_cli_help():
    result = run_cli('--help')
    assert result.returncode == 0
    assert 'taskops' in result.stdout.lower()


def test_cli_version():
    result = run_cli('--version')
    assert result.returncode == 0
    assert '0.1.0' in result.stdout


def test_cli_no_command_shows_help():
    result = run_cli()
    assert result.returncode == 1


def test_cli_init_help():
    result = run_cli('init', '--help')
    assert result.returncode == 0
    assert '--name' in result.stdout
    assert '--prefix' in result.stdout


def test_cli_all_commands_registered():
    result = run_cli('--help')
    for cmd in ['init', 'epic', 'task', 'objective', 'workflow', 'op', 'resource', 'query', 'setting']:
        assert cmd in result.stdout, f"Command '{cmd}' not found in help output"
