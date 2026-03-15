# TaskOps Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a skill-based project management tool that converts complex projects into ETS (Epic-Task-SubTask) structure for AI Agents.

**Architecture:** Skill-First approach — Skill documents (.md) serve as the primary entry point for AI Agents. Agents read skill instructions and call a Python CLI tool (`taskops.py`) to manage SQLite DB. Platform-specific differences (Claude Code hooks vs Gemini CLI instructions) are handled via separate skill files.

**Tech Stack:** Python 3.8+ (stdlib only — `sqlite3`, `argparse`, `json`, `string.Template`), SQLite, Bash (hooks), Markdown (skills/templates)

---

## Task 1: Project Scaffolding / 프로젝트 디렉토리 구조 생성

**Files:**
- Create: `cli/__init__.py`
- Create: `cli/taskops.py`
- Create: `cli/db/__init__.py`
- Create: `cli/db/schema.py`
- Create: `cli/db/connection.py`
- Create: `cli/commands/__init__.py`
- Create: `cli/commands/init.py`
- Create: `cli/commands/epic.py`
- Create: `cli/commands/task.py`
- Create: `cli/commands/objective.py`
- Create: `cli/commands/workflow.py`
- Create: `cli/commands/operation.py`
- Create: `cli/commands/resource.py`
- Create: `cli/commands/query.py`
- Create: `cli/commands/setting.py`
- Create: `cli/templates/TODO.md.tmpl`
- Create: `cli/templates/AGENTS.md.tmpl`
- Create: `cli/templates/SETTINGS.md.tmpl`
- Create: `cli/templates/TASK_OPERATIONS.md.tmpl`
- Create: `hooks/on_task_start.sh`
- Create: `hooks/on_tool_use.sh`
- Create: `hooks/on_task_complete.sh`
- Create: `skills/taskops.md`
- Create: `skills/taskops-gemini.md`
- Create: `skills/fragments/ets-planning.md`
- Create: `skills/fragments/workflow-guide.md`
- Create: `skills/fragments/monitoring-guide.md`
- Create: `tests/__init__.py`
- Create: `tests/test_db.py`
- Create: `tests/test_commands.py`

**Step 1: Create all directories**

```bash
mkdir -p cli/db cli/commands cli/templates hooks skills/fragments tests docs/usage
```

**Step 2: Create all `__init__.py` files**

```bash
touch cli/__init__.py cli/db/__init__.py cli/commands/__init__.py tests/__init__.py
```

**Step 3: Commit**

```bash
git add .
git commit -m "chore: scaffold project directory structure"
```

---

## Task 2: DB Module — Schema / DB 스키마 정의

**Files:**
- Create: `cli/db/schema.py`

**Step 1: Write the test**

```python
# tests/test_db.py
import sqlite3
import os
import tempfile
import pytest
from cli.db.schema import create_tables, SCHEMA_VERSION

def test_create_tables_creates_all_tables():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        conn = sqlite3.connect(db_path)
        create_tables(conn)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert 'tasks' in tables
        assert 'operations' in tables
        assert 'resources' in tables
        assert 'settings' in tables
        conn.close()
    finally:
        os.unlink(db_path)

def test_create_tables_is_idempotent():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    try:
        conn = sqlite3.connect(db_path)
        create_tables(conn)
        create_tables(conn)  # should not raise
        conn.close()
    finally:
        os.unlink(db_path)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_db.py -v`
Expected: FAIL with "cannot import name 'create_tables'"

**Step 3: Implement schema.py**

```python
# cli/db/schema.py
"""SQLite schema definition for TaskOps.
TaskOps DB 스키마 정의 모듈.
"""

SCHEMA_VERSION = 1

SQL_CREATE_TASKS = """
CREATE TABLE IF NOT EXISTS tasks (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL,
    type        TEXT NOT NULL CHECK(type IN ('project','epic','task','objective')),
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'todo'
                CHECK(status IN ('todo','in_progress','interrupted','done','cancelled')),
    parent_id   TEXT,
    todo        TEXT,
    interrupt   TEXT,
    milestone_target TEXT,
    due_date    TEXT,
    seq_order   INTEGER,
    parallel_group TEXT,
    depends_on  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

SQL_CREATE_OPERATIONS = """
CREATE TABLE IF NOT EXISTS operations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT NOT NULL,
    operation_type  TEXT NOT NULL
                    CHECK(operation_type IN ('start','progress','complete','error','interrupt')),
    agent_platform  TEXT,
    summary         TEXT,
    details         TEXT,
    subagent_used   INTEGER DEFAULT 0,
    subagent_result TEXT,
    started_at      TEXT,
    completed_at    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
"""

SQL_CREATE_RESOURCES = """
CREATE TABLE IF NOT EXISTS resources (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    description TEXT,
    res_type    TEXT NOT NULL DEFAULT 'reference'
                CHECK(res_type IN ('input','output','reference','intermediate')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
"""

SQL_CREATE_SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    description TEXT,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

SQL_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_tasks_project   ON tasks(project_id);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_parent    ON tasks(parent_id);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_type      ON tasks(type);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_status    ON tasks(status);",
    "CREATE INDEX IF NOT EXISTS idx_operations_task ON operations(task_id);",
    "CREATE INDEX IF NOT EXISTS idx_resources_task  ON resources(task_id);",
]


def create_tables(conn):
    """Create all tables and indexes. Idempotent.
    모든 테이블과 인덱스를 생성. 멱등성 보장.
    """
    conn.execute(SQL_CREATE_TASKS)
    conn.execute(SQL_CREATE_OPERATIONS)
    conn.execute(SQL_CREATE_RESOURCES)
    conn.execute(SQL_CREATE_SETTINGS)
    for idx_sql in SQL_CREATE_INDEXES:
        conn.execute(idx_sql)
    conn.commit()
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_db.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cli/db/schema.py tests/test_db.py
git commit -m "feat: add SQLite schema definition with 4 tables and indexes"
```

---

## Task 3: DB Module — Connection / DB 연결 관리

**Files:**
- Create: `cli/db/connection.py`

**Step 1: Write the test**

```python
# tests/test_db.py (append)
from cli.db.connection import get_connection, close_connection

def test_get_connection_creates_db_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        conn = get_connection(db_path)
        assert os.path.exists(db_path)
        close_connection(conn)

def test_get_connection_initializes_tables():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        conn = get_connection(db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert 'tasks' in tables
        close_connection(conn)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_db.py::test_get_connection_creates_db_file -v`
Expected: FAIL

**Step 3: Implement connection.py**

```python
# cli/db/connection.py
"""Database connection management.
DB 연결 관리 모듈.
"""
import sqlite3
from .schema import create_tables


def get_connection(db_path):
    """Open (or create) DB and ensure schema exists.
    DB를 열고 (또는 생성하고) 스키마가 존재하는지 확인.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    create_tables(conn)
    return conn


def close_connection(conn):
    """Close DB connection.
    DB 연결 종료.
    """
    if conn:
        conn.close()
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_db.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add cli/db/connection.py tests/test_db.py
git commit -m "feat: add DB connection manager with auto-initialization"
```

---

## Task 4: CLI Entry Point / CLI 진입점

**Files:**
- Create: `cli/taskops.py`

**Step 1: Write the test**

```python
# tests/test_commands.py
import subprocess
import sys

def test_cli_help():
    result = subprocess.run(
        [sys.executable, '-m', 'cli.taskops', '--help'],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert 'TaskOps' in result.stdout

def test_cli_version():
    result = subprocess.run(
        [sys.executable, '-m', 'cli.taskops', '--version'],
        capture_output=True, text=True
    )
    assert result.returncode == 0
```

**Step 2: Run test to verify it fails**

**Step 3: Implement taskops.py**

```python
# cli/taskops.py
"""TaskOps CLI entry point.
TaskOps CLI 진입점. argparse 기반 서브커맨드 라우팅.
"""
import argparse
import sys

__version__ = "0.1.0"


def build_parser():
    parser = argparse.ArgumentParser(
        prog='taskops',
        description='TaskOps — AI Agent project management tool (ETS 구조 기반 프로젝트 관리 도구)'
    )
    parser.add_argument('--version', action='version', version=f'taskops {__version__}')
    parser.add_argument('--db', type=str, default=None,
                        help='Path to SQLite DB file (DB 파일 경로)')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Each command module registers its subparser
    from .commands.init import register as register_init
    from .commands.epic import register as register_epic
    from .commands.task import register as register_task
    from .commands.objective import register as register_objective
    from .commands.workflow import register as register_workflow
    from .commands.operation import register as register_operation
    from .commands.resource import register as register_resource
    from .commands.query import register as register_query
    from .commands.setting import register as register_setting

    register_init(subparsers)
    register_epic(subparsers)
    register_task(subparsers)
    register_objective(subparsers)
    register_workflow(subparsers)
    register_operation(subparsers)
    register_resource(subparsers)
    register_query(subparsers)
    register_setting(subparsers)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Each command handler is set via set_defaults(func=handler)
    args.func(args)


if __name__ == '__main__':
    main()
```

**Step 4: Create stub command modules** (register function only, handlers empty)

Each command module in `cli/commands/` must have a `register(subparsers)` function. Create stubs for all 9 commands so the CLI can parse without error.

```python
# cli/commands/init.py (stub example — repeat pattern for all commands)
def register(subparsers):
    parser = subparsers.add_parser('init', help='Initialize a new project (프로젝트 초기화)')
    parser.set_defaults(func=handle)

def handle(args):
    print("init: not yet implemented")
```

**Step 5: Run tests**

Run: `python -m pytest tests/test_commands.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add cli/taskops.py cli/commands/*.py tests/test_commands.py
git commit -m "feat: add CLI entry point with argparse and command stubs"
```

---

## Task 5: `init` Command / 프로젝트 초기화 커맨드

**Files:**
- Modify: `cli/commands/init.py`
- Reference: `cli/templates/*.tmpl`

**Step 1: Write the test**

```python
# tests/test_commands.py (append)
import os
import tempfile
import json

def test_init_creates_project_structure():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = os.path.join(tmpdir, 'my-project')
        result = subprocess.run(
            [sys.executable, '-m', 'cli.taskops', 'init',
             '--name', 'My Project', '--prefix', 'TOS', '--path', project_path],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert os.path.exists(os.path.join(project_path, 'taskops.db'))
        assert os.path.exists(os.path.join(project_path, 'TODO.md'))
        assert os.path.exists(os.path.join(project_path, 'AGENTS.md'))
        assert os.path.exists(os.path.join(project_path, 'SETTINGS.md'))
        assert os.path.exists(os.path.join(project_path, 'TASK_OPERATIONS.md'))
        assert os.path.isdir(os.path.join(project_path, 'resources'))
```

**Step 2: Run test to verify it fails**

**Step 3: Create template files**

```
# cli/templates/TODO.md.tmpl
# ${project_name} (${prefix})

> Generated by TaskOps | Last updated: ${timestamp}

## Workflow / 실행 순서

(No tasks yet / 아직 등록된 작업이 없습니다)

## Objectives / 목표

(No objectives yet / 아직 등록된 목표가 없습니다)
```

```
# cli/templates/AGENTS.md.tmpl
# ${project_name}

> Managed by TaskOps

## Project Info
- Prefix: ${prefix}
- DB: taskops.db
- Created: ${timestamp}

## Files
- TODO.md: Workflow and ETS status (작업 현황)
- TASK_OPERATIONS.md: Operation logs (작업 이력)
- SETTINGS.md: Agent behavior guidelines (에이전트 행동 지침)
- resources/: Intermediate files (중간 결과물)
```

```
# cli/templates/SETTINGS.md.tmpl
# Project Settings

> AI Agent 행동 지침 / Agent Behavior Guidelines

## General / 일반

- autonomy_level: moderate
- commit_style: conventional

## Execution / 실행

- use_subagent: true
- parallel_execution: true

## Monitoring / 모니터링

- progress_interval: major_steps
```

```
# cli/templates/TASK_OPERATIONS.md.tmpl
# Task Operations Log

> Generated by TaskOps | Last updated: ${timestamp}

(No operations yet / 아직 기록된 작업이 없습니다)
```

**Step 4: Implement init command**

```python
# cli/commands/init.py
"""Project initialization command.
프로젝트 초기화 커맨드. 폴더, DB, 템플릿 파일을 생성.
"""
import os
from datetime import datetime
from string import Template

from ..db.connection import get_connection, close_connection


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')

DEFAULT_SETTINGS = [
    ('autonomy_level', 'moderate', 'Agent autonomy level (low|moderate|high)'),
    ('commit_style', 'conventional', 'Commit message style'),
    ('use_subagent', 'true', 'Allow sub agent usage'),
    ('parallel_execution', 'true', 'Allow parallel task execution'),
    ('progress_interval', 'major_steps', 'Progress log interval (every_tool|major_steps|start_end_only)'),
]


def register(subparsers):
    parser = subparsers.add_parser('init', help='Initialize a new project (프로젝트 초기화)')
    parser.add_argument('--name', required=True, help='Project name')
    parser.add_argument('--prefix', required=True, help='Task ID prefix (e.g. TOS)')
    parser.add_argument('--path', default='.', help='Project folder path (default: cwd)')
    parser.set_defaults(func=handle)


def handle(args):
    project_path = os.path.abspath(args.path)
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, 'resources'), exist_ok=True)

    # Create DB
    db_path = os.path.join(project_path, 'taskops.db')
    conn = get_connection(db_path)

    # Insert project record
    now = datetime.now().isoformat(sep=' ', timespec='seconds')
    conn.execute(
        "INSERT OR IGNORE INTO tasks (id, project_id, type, title, status, created_at, updated_at) "
        "VALUES (?, ?, 'project', ?, 'in_progress', ?, ?)",
        (args.prefix, args.prefix, args.name, now, now)
    )

    # Insert default settings
    for key, value, desc in DEFAULT_SETTINGS:
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value, description, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (key, value, desc, now)
        )
    conn.commit()

    # Generate template files
    template_vars = {
        'project_name': args.name,
        'prefix': args.prefix,
        'timestamp': now,
    }
    for tmpl_name in ['TODO.md.tmpl', 'AGENTS.md.tmpl', 'SETTINGS.md.tmpl', 'TASK_OPERATIONS.md.tmpl']:
        tmpl_path = os.path.join(TEMPLATE_DIR, tmpl_name)
        out_name = tmpl_name.replace('.tmpl', '')
        out_path = os.path.join(project_path, out_name)
        with open(tmpl_path, 'r', encoding='utf-8') as f:
            tmpl = Template(f.read())
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(tmpl.safe_substitute(template_vars))

    close_connection(conn)
    print(f"Project '{args.name}' initialized at {project_path}")
    print(f"  Prefix: {args.prefix}")
    print(f"  DB: {db_path}")
```

**Step 5: Run tests**

Run: `python -m pytest tests/test_commands.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add cli/commands/init.py cli/templates/*.tmpl tests/test_commands.py
git commit -m "feat: implement init command with DB, templates, and project setup"
```

---

## Task 6: `epic` Command / Epic 관리 커맨드

**Files:**
- Modify: `cli/commands/epic.py`

**Step 1: Write tests for epic create/list/show/update/delete**

**Step 2: Implement epic.py**

Key behaviors:
- `epic create --title "..." [--description "..."]`: ID 자동 생성 (`{PREFIX}-E{NNN}`), tasks 테이블에 `type='epic'` 삽입
- `epic list`: 모든 Epic 목록 출력 (id, title, status)
- `epic show {ID}`: Epic 상세 정보 + 하위 Task 목록
- `epic update {ID} --status {status} [--title "..."]`: 필드 업데이트
- `epic delete {ID}`: 레코드 삭제 (하위 Task 존재 시 경고)

ID 생성 로직: `SELECT MAX(CAST(SUBSTR(id, INSTR(id,'-E')+2) AS INTEGER)) FROM tasks WHERE project_id=? AND type='epic'` → +1 → 3자리 패딩

**Step 3: Run tests, verify PASS**

**Step 4: Commit**

```bash
git add cli/commands/epic.py tests/
git commit -m "feat: implement epic CRUD command"
```

---

## Task 7: `task` Command / Task/SubTask 관리 커맨드

**Files:**
- Modify: `cli/commands/task.py`

**Step 1: Write tests for task create/list/show/update/delete**

**Step 2: Implement task.py**

Key behaviors:
- `task create --parent {EPIC_OR_TASK_ID} --title "..." [--todo "..."] [--description "..."]`: ID 자동 생성 (`{PREFIX}-T{NNN}`), `parent_id` 설정
- `task list [--epic {ID}] [--status {status}] [--parent {ID}]`: 필터링된 Task 목록
- `task show {ID}`: Task 상세 + SubTask 목록
- `task update {ID} --status {status} [--interrupt "..."] [--title "..."] [--todo "..."]`: 상태 변경 시 `updated_at` 갱신, `interrupted` 시 `interrupt` 필드 필수
- `task delete {ID}`: 삭제 (하위 SubTask 존재 시 경고)

ID 생성: Epic과 동일 패턴, `T` prefix, Task/SubTask 동일 시퀀스.

**Step 3: Run tests, verify PASS**

**Step 4: Commit**

```bash
git add cli/commands/task.py tests/
git commit -m "feat: implement task CRUD command (Task + SubTask)"
```

---

## Task 8: `objective` Command / Objective 관리 커맨드

**Files:**
- Modify: `cli/commands/objective.py`

**Step 1: Write tests**

**Step 2: Implement objective.py**

Key behaviors:
- `objective create --title "..." [--milestone "..."] [--due-date "YYYY-MM-DD"]`: ID `{PREFIX}-O{NNN}`, `type='objective'`
- `objective list`: Objective 목록 (title, milestone/due_date, status)
- `objective update {ID} --status {status}`: 상태 변경
- `objective delete {ID}`: 삭제

**Step 3: Run tests, verify PASS**

**Step 4: Commit**

```bash
git add cli/commands/objective.py tests/
git commit -m "feat: implement objective CRUD command"
```

---

## Task 9: `workflow` Command / Workflow 관리 커맨드

**Files:**
- Modify: `cli/commands/workflow.py`

**Step 1: Write tests**

**Step 2: Implement workflow.py**

Key behaviors:
- `workflow set-order {ID1} {ID2} ...`: 각 Task의 `seq_order`를 1, 2, 3, ... 으로 업데이트
- `workflow set-parallel --group {name} {ID1} {ID2} ...`: `parallel_group` 설정
- `workflow add-dep {ID} --depends-on {ID1} {ID2} ...`: `depends_on` JSON 배열에 추가
- `workflow show`: 전체 workflow를 순서대로 출력 (병렬 그룹 표시)
- `workflow next`: 실행 가능한 다음 Task 목록 반환 (status=todo + depends_on 충족)
- `workflow current`: 현재 in_progress인 Task 반환 (Hook에서 사용)

`workflow next` SQL 쿼리:
```sql
SELECT id, title FROM tasks
WHERE status = 'todo' AND type = 'task'
  AND (depends_on IS NULL OR NOT EXISTS (
    SELECT 1 FROM json_each(depends_on) AS dep
    JOIN tasks AS t ON t.id = dep.value WHERE t.status != 'done'
  ))
ORDER BY seq_order ASC;
```

**Step 3: Run tests, verify PASS**

**Step 4: Commit**

```bash
git add cli/commands/workflow.py tests/
git commit -m "feat: implement workflow management command"
```

---

## Task 10: `op` Command / Operations 기록 커맨드

**Files:**
- Modify: `cli/commands/operation.py`

**Step 1: Write tests**

**Step 2: Implement operation.py**

Key behaviors:
- `op start {TASK_ID} [--platform {name}]`: operations 레코드 생성, `operation_type='start'`, `started_at` 기록
- `op progress {TASK_ID} --summary "..." [--details '{json}'] [--subagent]`: `operation_type='progress'`
- `op complete {TASK_ID} --summary "..." [--details '{json}']`: `operation_type='complete'`, `completed_at` 기록
- `op error {TASK_ID} --summary "..."`: `operation_type='error'`
- `op interrupt {TASK_ID} --summary "..."`: `operation_type='interrupt'`
- `op log [--task {ID}]`: operations 이력 출력

**Step 3: Run tests, verify PASS**

**Step 4: Commit**

```bash
git add cli/commands/operation.py tests/
git commit -m "feat: implement operation logging command"
```

---

## Task 11: `resource` Command / Resource 관리 커맨드

**Files:**
- Modify: `cli/commands/resource.py`

**Step 1: Write tests**

**Step 2: Implement resource.py**

Key behaviors:
- `resource add {TASK_ID} --path {path} --type {input|output|reference|intermediate} [--desc "..."]`: resources 테이블에 삽입
- `resource list [--task {ID}] [--type {type}]`: 리소스 목록

**Step 3: Run tests, verify PASS**

**Step 4: Commit**

```bash
git add cli/commands/resource.py tests/
git commit -m "feat: implement resource management command"
```

---

## Task 12: `query` Command / 상태 조회 커맨드

**Files:**
- Modify: `cli/commands/query.py`

**Step 1: Write tests**

**Step 2: Implement query.py**

Key behaviors:
- `query status`: 프로젝트 전체 요약 (총 Epic/Task 수, 상태별 카운트, 진행률)
- `query tasks [--status {status}]`: 필터링된 Task 목록
- `query generate-todo`: DB에서 TODO.md 재생성 (Workflow 섹션 + ETS 체크박스 + Objective)
- `query generate-ops`: DB에서 TASK_OPERATIONS.md 재생성

`generate-todo` 로직:
1. tasks 테이블에서 workflow 순서대로 Task 조회
2. Epic별로 그룹핑
3. 체크박스 + ID + 제목 + 상태 백틱으로 포매팅
4. Objective 섹션 추가
5. TODO.md 파일로 출력

**Step 3: Run tests, verify PASS**

**Step 4: Commit**

```bash
git add cli/commands/query.py tests/
git commit -m "feat: implement query and report generation command"
```

---

## Task 13: `setting` Command / 설정 관리 커맨드

**Files:**
- Modify: `cli/commands/setting.py`

**Step 1: Write tests**

**Step 2: Implement setting.py**

Key behaviors:
- `setting set {key} {value} [--desc "..."]`: settings 테이블에 upsert + SETTINGS.md 재생성
- `setting get {key}`: 설정값 출력
- `setting list`: 전체 설정 목록
- `setting delete {key}`: 설정 삭제 + SETTINGS.md 재생성

SETTINGS.md 재생성: settings 테이블에서 전체 조회 → 카테고리별 그룹핑 → 마크다운 출력

**Step 3: Run tests, verify PASS**

**Step 4: Commit**

```bash
git add cli/commands/setting.py tests/
git commit -m "feat: implement setting management command"
```

---

## Task 14: Hook Scripts / Claude Code Hook 스크립트

**Files:**
- Create: `hooks/on_task_start.sh`
- Create: `hooks/on_tool_use.sh`
- Create: `hooks/on_task_complete.sh`

**Step 1: Implement on_task_start.sh**

```bash
#!/bin/bash
# Hook: Called when agent starts a task
# TaskOps Hook: Task 시작 시 호출
TASK_ID="$1"
TASKOPS_CLI="$(dirname "$0")/../cli/taskops.py"
python "$TASKOPS_CLI" task update "$TASK_ID" --status in_progress
python "$TASKOPS_CLI" op start "$TASK_ID" --platform claude_code
```

**Step 2: Implement on_tool_use.sh**

```bash
#!/bin/bash
# Hook: Called after tool use (Edit, Write, Bash)
# TaskOps Hook: 도구 사용 후 진행 상황 기록
TASKOPS_CLI="$(dirname "$0")/../cli/taskops.py"
ACTIVE_TASK=$(python "$TASKOPS_CLI" workflow current 2>/dev/null)
if [ -n "$ACTIVE_TASK" ]; then
    python "$TASKOPS_CLI" op progress "$ACTIVE_TASK" \
        --summary "Tool used: ${TOOL_NAME:-unknown}"
fi
```

**Step 3: Implement on_task_complete.sh**

```bash
#!/bin/bash
# Hook: Called when agent completes a task
# TaskOps Hook: Task 완료 시 호출
TASK_ID="$1"
TASKOPS_CLI="$(dirname "$0")/../cli/taskops.py"
python "$TASKOPS_CLI" task update "$TASK_ID" --status done
python "$TASKOPS_CLI" op complete "$TASK_ID" --summary "Task completed"
python "$TASKOPS_CLI" query generate-todo
```

**Step 4: Make executable**

```bash
chmod +x hooks/*.sh
```

**Step 5: Commit**

```bash
git add hooks/
git commit -m "feat: add Claude Code hook scripts for task monitoring"
```

---

## Task 15: Skill Documents — Claude Code / Claude Code 용 Skill 문서

**Files:**
- Create: `skills/taskops.md`
- Create: `skills/fragments/ets-planning.md`
- Create: `skills/fragments/workflow-guide.md`
- Create: `skills/fragments/monitoring-guide.md`

**Step 1: Write `skills/taskops.md`**

Main skill document with:
- Frontmatter (name, description)
- When to Use / Prerequisites
- Phase 1-4 instructions referencing CLI commands
- Hook integration instructions
- English + Korean comments

**Step 2: Write fragment files**

- `ets-planning.md`: ETS decomposition rules, ID naming, hierarchy rules
- `workflow-guide.md`: Sequential/parallel workflow definition, dependency rules
- `monitoring-guide.md`: When to record operations, what to include, format

**Step 3: Commit**

```bash
git add skills/
git commit -m "feat: add Claude Code skill document and instruction fragments"
```

---

## Task 16: Skill Documents — Gemini CLI / Gemini CLI 용 Skill 문서

**Files:**
- Create: `skills/taskops-gemini.md`

**Step 1: Write `skills/taskops-gemini.md`**

Same 4-phase structure as Claude Code skill, with:
- No Hook references — instead, explicit CLI call instructions for operations recording
- Gemini CLI tool name mapping
- English + Korean comments

**Step 2: Commit**

```bash
git add skills/taskops-gemini.md
git commit -m "feat: add Gemini CLI skill document"
```

---

## Task 17: Documentation / 문서 작성

**Files:**
- Create: `docs/usage/quickstart.md`
- Create: `docs/usage/commands.md`
- Update: `README.md`

**Step 1: Write quickstart.md**

Installation (git clone) → First project setup → Basic usage flow

**Step 2: Write commands.md**

All CLI commands with full option reference

**Step 3: Write README.md**

Project overview, features, installation, quick start, links to docs

**Step 4: Commit**

```bash
git add docs/usage/ README.md
git commit -m "docs: add quickstart guide, command reference, and README"
```

---

## Task 18: Integration Test / 통합 테스트

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write end-to-end test**

Full lifecycle test:
1. `init` → project created
2. `epic create` → epic exists in DB
3. `task create` (under epic) → task exists
4. `task create` (under task = subtask) → subtask exists
5. `objective create` → objective exists
6. `workflow set-order` → seq_order set
7. `workflow next` → returns first task
8. `op start` → operation recorded
9. `op progress` → progress recorded
10. `task update --status done` → status changed
11. `op complete` → completion recorded
12. `query status` → summary correct
13. `query generate-todo` → TODO.md regenerated with correct content

**Step 2: Run test**

Run: `python -m pytest tests/test_integration.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add end-to-end integration test for full project lifecycle"
```

---

## Task 19: Final Review & Polish / 최종 검토

**Step 1: Run all tests**

```bash
python -m pytest tests/ -v
```

**Step 2: Verify CLI help for all commands**

```bash
python -m cli.taskops --help
python -m cli.taskops init --help
python -m cli.taskops epic --help
# ... (all commands)
```

**Step 3: Test a real project flow manually**

```bash
python cli/taskops.py init --name "Test Project" --prefix TST --path /tmp/test-project
python cli/taskops.py epic create --title "First Epic"
python cli/taskops.py task create --parent TST-E001 --title "First Task"
python cli/taskops.py workflow set-order TST-T001
python cli/taskops.py workflow next
python cli/taskops.py op start TST-T001
python cli/taskops.py op complete TST-T001 --summary "Done"
python cli/taskops.py query status
python cli/taskops.py query generate-todo
```

**Step 4: Update CLAUDE.md and AGENTS.md with final status**

**Step 5: Commit**

```bash
git add .
git commit -m "chore: final review and polish"
```

---

## Summary / 요약

| Task | Description | Dependencies |
|------|-------------|-------------|
| 1 | Project Scaffolding | — |
| 2 | DB Schema | 1 |
| 3 | DB Connection | 2 |
| 4 | CLI Entry Point | 3 |
| 5 | init Command | 4 |
| 6 | epic Command | 4 |
| 7 | task Command | 4 |
| 8 | objective Command | 4 |
| 9 | workflow Command | 4 |
| 10 | op Command | 4 |
| 11 | resource Command | 4 |
| 12 | query Command | 6, 7, 8, 9, 10 |
| 13 | setting Command | 4 |
| 14 | Hook Scripts | 9, 10 |
| 15 | Skill Doc — Claude Code | 5-13 |
| 16 | Skill Doc — Gemini CLI | 15 |
| 17 | Documentation | 15, 16 |
| 18 | Integration Test | 5-13 |
| 19 | Final Review | 17, 18 |
