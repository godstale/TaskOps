"""Unit tests for workflow import command.
workflow import 커맨드 유닛 테스트.
"""
import json
import os
import subprocess
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}

SAMPLE = json.dumps({
    "epics": [
        {
            "title": "Phase 1: Setup",
            "tasks": [
                {
                    "title": "Init project",
                    "description": "Set up structure",
                    "subtasks": [{"title": "Create folders"}]
                },
                {"title": "Write tests"}
            ]
        },
        {
            "title": "Phase 2: Core",
            "tasks": [{"title": "Implement API"}]
        }
    ]
})


def run_cli(*args):
    return subprocess.run(
        [sys.executable, '-m', 'cli', *args],
        capture_output=True, encoding='utf-8', errors='replace',
        cwd=PROJECT_ROOT, env=ENV
    )


def setup_with_workflow(tmpdir):
    pp = os.path.join(tmpdir, 'proj')
    run_cli('init', '--name', 'Test', '--prefix', 'TST', '--path', pp)
    db = os.path.join(pp, 'taskops.db')
    run_cli('--db', db, 'workflow', 'create', '--title', 'My List')
    return pp, db


def test_import_creates_epics():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_with_workflow(d)
        r = run_cli('--db', db, 'workflow', 'import', 'TST-W001', '--structure', SAMPLE)
        assert r.returncode == 0
        assert 'TST-E001' in r.stdout
        assert 'Phase 1: Setup' in r.stdout
        assert 'TST-E002' in r.stdout
        assert 'Phase 2: Core' in r.stdout


def test_import_creates_tasks():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_with_workflow(d)
        r = run_cli('--db', db, 'workflow', 'import', 'TST-W001', '--structure', SAMPLE)
        assert r.returncode == 0
        assert 'TST-T001' in r.stdout
        assert 'Init project' in r.stdout
        assert 'TST-T003' in r.stdout
        assert 'Write tests' in r.stdout


def test_import_creates_subtasks():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_with_workflow(d)
        r = run_cli('--db', db, 'workflow', 'import', 'TST-W001', '--structure', SAMPLE)
        assert r.returncode == 0
        assert 'TST-T002' in r.stdout
        assert 'Create folders' in r.stdout


def test_import_replaces_on_reimport():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_with_workflow(d)
        run_cli('--db', db, 'workflow', 'import', 'TST-W001', '--structure', SAMPLE)
        new_structure = json.dumps({
            "epics": [{"title": "Only Epic", "tasks": [{"title": "Only Task"}]}]
        })
        r = run_cli('--db', db, 'workflow', 'import', 'TST-W001', '--structure', new_structure)
        assert r.returncode == 0
        assert 'Phase 1: Setup' not in r.stdout
        assert 'Only Epic' in r.stdout


def test_import_invalid_workflow_id():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_with_workflow(d)
        r = run_cli('--db', db, 'workflow', 'import', 'TST-W999', '--structure', SAMPLE)
        assert r.returncode != 0


def test_import_invalid_json():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_with_workflow(d)
        r = run_cli('--db', db, 'workflow', 'import', 'TST-W001', '--structure', 'not-json')
        assert r.returncode != 0


def test_import_from_file():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_with_workflow(d)
        struct_file = os.path.join(d, 'structure.json')
        with open(struct_file, 'w') as f:
            f.write(SAMPLE)
        r = run_cli('--db', db, 'workflow', 'import', 'TST-W001',
                    '--structure-file', struct_file)
        assert r.returncode == 0
        assert 'TST-E001' in r.stdout


def test_import_tasks_have_seq_order():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_with_workflow(d)
        run_cli('--db', db, 'workflow', 'import', 'TST-W001', '--structure', SAMPLE)
        # workflow next should return first task
        r = run_cli('--db', db, 'workflow', 'next')
        assert r.returncode == 0
        assert 'TST-T001' in r.stdout


def test_import_workflow_header_in_output():
    with tempfile.TemporaryDirectory() as d:
        pp, db = setup_with_workflow(d)
        r = run_cli('--db', db, 'workflow', 'import', 'TST-W001', '--structure', SAMPLE)
        assert 'TST-W001' in r.stdout
        assert 'My List' in r.stdout
