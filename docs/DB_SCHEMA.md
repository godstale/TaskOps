# TaskOps DB Schema Reference

> Schema Version: 3
> DB Engine: SQLite (Python built-in `sqlite3`)
> File: `taskops.db` (created in project root by `python -m cli init`)

---

## Table Overview

| Table | Purpose |
|-------|---------|
| `tasks` | All ETS components: Project, Epic, Task/SubTask, Objective |
| `workflows` | Logical groupings of tasks (one per TODO list) |
| `operations` | AI agent activity log per task |
| `resources` | File references associated with tasks |
| `settings` | Project-level key-value configuration |
| `checkpoints` | Task status snapshots for rollback |

---

## tasks

모든 ETS 컴포넌트를 단일 테이블로 저장. `type` 필드로 구분.

```sql
CREATE TABLE tasks (
    id               TEXT PRIMARY KEY,
    project_id       TEXT NOT NULL,
    type             TEXT NOT NULL CHECK(type IN ('project','epic','task','objective')),
    title            TEXT NOT NULL,
    description      TEXT,
    status           TEXT NOT NULL DEFAULT 'todo'
                     CHECK(status IN ('todo','in_progress','interrupted','done','cancelled')),
    parent_id        TEXT,
    workflow_id      TEXT,                      -- references workflows(id), nullable
    todo             TEXT,                      -- per-task implementation notes (markdown)
    interrupt        TEXT,                      -- reason when status='interrupted'

    -- Objective-only fields
    milestone_target TEXT,
    due_date         TEXT,                      -- ISO 8601: 2026-03-20

    -- Workflow ordering
    seq_order        INTEGER,                   -- execution order (ORDER BY seq_order)
    parallel_group   TEXT,                      -- same group = concurrent execution allowed
    depends_on       TEXT,                      -- JSON array of task IDs: '["PRJ-T001"]'

    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### type 별 parent_id 규칙

| type | parent_id |
|------|-----------|
| `project` | NULL |
| `epic` | `{PREFIX}` (project ID) |
| `task` | Epic ID (`{PREFIX}-E001`) |
| `task` (SubTask) | Task ID (`{PREFIX}-T001`) |
| `objective` | `{PREFIX}` (project ID) |

### ID 체계

| type | 형식 | 예시 |
|------|------|------|
| project | `{PREFIX}` | `TOS` |
| epic | `{PREFIX}-E{NNN}` | `TOS-E001` |
| task / subtask | `{PREFIX}-T{NNN}` | `TOS-T001` |
| objective | `{PREFIX}-O{NNN}` | `TOS-O001` |

Task와 SubTask는 동일 시퀀스(`T`)를 사용. `parent_id`로 SubTask 여부 판별.

### status 전이

```
todo → in_progress → done
          │
          └→ interrupted → in_progress (재시작)
          └→ cancelled
```

### workflow_id / seq_order / parallel_group / depends_on

| 필드 | 역할 |
|------|------|
| `workflow_id` | 이 Task가 속한 Workflow ID (`NULL` = 미분류) |
| `seq_order` | 전체 실행 순서 (정수). `ORDER BY seq_order` |
| `parallel_group` | 동일 값이면 동시 실행 가능. `NULL`이면 단독 순차 실행 |
| `depends_on` | JSON 배열. 이 Task 실행 전에 완료되어야 할 Task ID 목록 |

**실행 가능 조건:**
```
status = 'todo'
AND (depends_on IS NULL OR 모든 의존 Task의 status = 'done')
```

---

## workflows

```sql
CREATE TABLE workflows (
    id          TEXT PRIMARY KEY,              -- {PREFIX}-W001
    project_id  TEXT NOT NULL,
    title       TEXT NOT NULL,                 -- 워크플로우 이름 (예: TODO 파일명)
    source_file TEXT,                          -- 원본 TODO 파일 경로 (선택)
    status      TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active','completed','archived')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES tasks(id)
);
```

### ID 체계

| 형식 | 예시 |
|------|------|
| `{PREFIX}-W{NNN}` | `TOS-W001` |

### TODO 리스트 → Workflow 대응

```
TODO 파일 1개  ←→  Workflow 1개
  ## Section  ←→  Epic
  - [ ] item  ←→  Task
  - [ ] item  ←→  SubTask (중첩 시)
```

`workflow import` 로 JSON 구조를 일괄 입력. 재import 시 해당 Workflow의 기존 Task를 삭제 후 재생성 (replace semantics).

---

## operations

AI Agent의 작업 처리 이력. Task 하나에 여러 레코드 가능 (start → progress → complete).

```sql
CREATE TABLE operations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id          TEXT NOT NULL,
    operation_type   TEXT NOT NULL
                     CHECK(operation_type IN ('start','progress','complete','error','interrupt')),
    agent_platform   TEXT,                     -- 'claude_code' | 'gemini_cli'
    summary          TEXT,                     -- 진행 요약 또는 완료 메시지
    details          TEXT,                     -- JSON (파일 목록, 도구 사용 내역 등)
    subagent_used    INTEGER DEFAULT 0,        -- 0 | 1
    subagent_result  TEXT,
    tool_name        TEXT,                     -- 사용된 도구명
    skill_name       TEXT,                     -- 사용된 스킬명
    mcp_name         TEXT,                     -- 사용된 MCP명
    retry_count      INTEGER DEFAULT 0,
    input_tokens     INTEGER,
    output_tokens    INTEGER,
    duration_seconds INTEGER,
    started_at       TEXT,
    completed_at     TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

### operation_type 흐름

```
start → progress (0회 이상) → complete
                            → error
                            → interrupt
```

---

## resources

Task 처리 중 참조하거나 생성되는 파일 경로 기록.

```sql
CREATE TABLE resources (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    description TEXT,
    res_type    TEXT NOT NULL DEFAULT 'reference'
                CHECK(res_type IN ('input','output','reference','intermediate')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

### res_type 설명

| 값 | 의미 |
|----|------|
| `input` | 작업 시작 시 전달되는 참고 자료 |
| `output` | 작업 결과물 |
| `reference` | 참조 문서 (읽기 전용) |
| `intermediate` | 중간 산출물 |

---

## settings

프로젝트 설정 키-값 저장. 파일(`SETTINGS.md`) 없이 DB에만 관리.

```sql
CREATE TABLE settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    description TEXT,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 기본 설정값 (init 시 자동 삽입)

| key | 기본값 | 설명 |
|-----|--------|------|
| `autonomy_level` | `moderate` | Agent 자율성 수준 (`low\|moderate\|high`) |
| `commit_style` | `conventional` | 커밋 메시지 스타일 |
| `use_subagent` | `true` | Sub Agent 사용 허용 여부 |
| `parallel_execution` | `true` | 병렬 Task 동시 실행 허용 여부 |
| `progress_interval` | `major_steps` | 진행 기록 간격 (`every_tool\|major_steps\|start_end_only`) |
| `__schema_version` | `3` | DB 스키마 버전 (내부 사용) |

---

## checkpoints

특정 시점의 Task 상태 스냅샷. 롤백에 사용.

```sql
CREATE TABLE checkpoints (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    note        TEXT,
    snapshot    TEXT NOT NULL,   -- JSON: {task_id: {status, interrupt}, ...}
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

`snapshot` JSON 예시:
```json
{
  "TOS-T001": {"status": "done", "interrupt": null},
  "TOS-T002": {"status": "in_progress", "interrupt": null},
  "TOS-T003": {"status": "todo", "interrupt": null}
}
```

---

## Indexes

```sql
CREATE INDEX idx_tasks_project    ON tasks(project_id);
CREATE INDEX idx_tasks_parent     ON tasks(parent_id);
CREATE INDEX idx_tasks_type       ON tasks(type);
CREATE INDEX idx_tasks_status     ON tasks(status);
CREATE INDEX idx_workflows_project ON workflows(project_id);
CREATE INDEX idx_operations_task  ON operations(task_id);
CREATE INDEX idx_resources_task   ON resources(task_id);
```

---

## Schema Migration History

| Version | 변경 내용 |
|---------|---------|
| v1 | 초기 스키마 (tasks, operations, resources, settings) |
| v2 | operations에 `tool_name`, `skill_name`, `mcp_name`, `retry_count`, `input_tokens`, `output_tokens`, `duration_seconds` 추가 |
| v3 | `workflows` 테이블 추가, `tasks.workflow_id` 컬럼 추가, `checkpoints` 테이블 추가 |

마이그레이션은 `cli/db/schema.py`의 `migrate_schema()` 함수가 자동 처리. DB 연결 시 버전 확인 후 미적용 마이그레이션을 순서대로 실행.
