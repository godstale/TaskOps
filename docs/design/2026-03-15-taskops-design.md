# TaskOps Skill Design Document

> Date: 2026-03-15
> Status: In Progress (설계 진행 중)

---

## 1. Overview / 개요

TaskOps는 Claude Code, Gemini CLI 등의 AI Agent에서 사용하는 skill로,
복잡한 프로젝트를 ETS(Epic-Task-SubTask) 구조로 분해하고 관리하여
자동화된 작업 처리를 지원합니다.

---

## 2. Design Decisions / 설계 결정 사항

아래는 기획 과정에서 질의응답을 통해 확정된 결정 사항입니다.

| # | 항목 | 결정 | 비고 |
|---|------|------|------|
| 1 | 타깃 플랫폼 | Claude Code + Gemini CLI 동시 지원 | 플랫폼별 skill 파일 분리 |
| 2 | DB 관리 | Python 스크립트 기반 (`sqlite3` 내장 모듈) | 외부 의존성 없음 |
| 3 | 배포 구조 | Git 저장소 기반 | 사용자가 클론 후 skill 경로 등록 |
| 4 | 프로젝트 폴더 위치 | 사용자 지정 (기본값: cwd) | 초기화 시 경로 지정 |
| 5 | Task ID 체계 | `{PREFIX}-E001` (Epic), `{PREFIX}-T001` (Task/SubTask) | Task와 SubTask는 동일 시퀀스 |
| 6 | Workflow 정의 | 혼합 방식 (순차 리스트 + 그룹 병렬) | 기본 순차, 필요 시 병렬 그룹 |
| 7 | Operations 기록 | Hook(Claude Code) + Skill 지침(Gemini CLI) 혼합 | 플랫폼별 상이 |
| 8 | Objective | 마일스톤 + 날짜 기반 이벤트 모두 지원 | 작업 진행과 직접 관련 없는 표식 |
| 9 | Settings | AI Agent 행동 지침 위주 | SETTINGS.md에 저장 |
| 10 | Resource 관리 | DB에 경로 참조 + 중간 결과물은 `resources/` 디렉토리 | 자동 생성 파일은 resources/에 저장 |
| 11 | TODO.md 형식 | Workflow는 순서 리스트, ETS 상세는 체크박스 + 메타데이터 | 혼합 형식 |
| 12 | Rollback | 상태 롤백만 (DB 상태 변경) | Agent가 Python CLI로 상태 변경 |
| 13 | Python 인터페이스 | 단일 CLI(`taskops.py`) + 내부 모듈 분리 | argparse 기반 서브커맨드 |
| 14 | Hook 범위 | 상태 변경 + 진행률 추적 | 도구 사용 시에도 기록 |
| 15 | Skill 문서 언어 | 영어 + 한국어 주석 | 글로벌 호환 + 한국어 설명 |

---

## 3. Architecture Approach / 아키텍처 접근 방식

**선택: Approach A — Skill-First**

Skill 문서(.md)가 핵심 진입점. Agent가 Skill을 읽고 지침에 따라 Python CLI를 호출하는 방식.

**선택 이유:**
1. Agent가 skill 문서를 읽고 그대로 따르는 것이 가장 신뢰성이 높음
2. 플랫폼별 차이는 skill 파일만 분리하면 해결
3. 구조가 단순하여 사용자가 이해하고 커스터마이즈하기 쉬움
4. Git 저장소 기반 배포와 가장 잘 맞음

**비교한 대안:**
- Approach B (CLI-First): CLI 중심, skill은 사용법 가이드만. Agent 순응도가 낮을 수 있음.
- Approach C (Hybrid): 기능별 skill 분리. 컨텍스트 절약 가능하나 복잡도 증가.

---

## 4. Repository Structure / 저장소 구조

```
taskops/
├── skills/                        # Skill 문서
│   ├── taskops.md                 # 메인 skill (Claude Code용)
│   ├── taskops-gemini.md          # Gemini CLI용 skill
│   └── fragments/                 # 공통 지침 조각 (중복 방지)
│       ├── ets-planning.md        # ETS 구조 생성 지침
│       ├── workflow-guide.md      # Workflow 정의 지침
│       └── monitoring-guide.md    # 모니터링/기록 지침
│
├── cli/                           # Python CLI 도구
│   ├── taskops.py                 # 진입점 (argparse 기반)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── schema.py              # SQLite 스키마 정의 및 마이그레이션
│   │   └── connection.py          # DB 연결 관리
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── init.py                # 프로젝트 초기화
│   │   ├── task.py                # Task CRUD (create, read, update, delete)
│   │   ├── epic.py                # Epic CRUD
│   │   ├── objective.py           # Objective CRUD
│   │   ├── workflow.py            # Workflow 관리
│   │   ├── operation.py           # Operations 기록 (시작/진행/완료)
│   │   ├── resource.py            # Resource 등록/조회
│   │   └── query.py               # 상태 조회/리포트
│   └── templates/
│       ├── TODO.md.tmpl           # TODO.md 템플릿
│       ├── AGENTS.md.tmpl         # AGENTS.md 템플릿
│       ├── SETTINGS.md.tmpl       # SETTINGS.md 템플릿
│       └── TASK_OPERATIONS.md.tmpl # 작업 이력 템플릿
│
├── hooks/                         # Claude Code hooks
│   ├── on_task_start.sh           # Task 시작 시 operations 기록
│   ├── on_tool_use.sh             # 도구 사용 시 진행률 기록
│   └── on_task_complete.sh        # Task 완료 시 기록
│
├── docs/
│   ├── plan/
│   │   ├── BUSINESS_LOGIC.md      # 비즈니스 로직 정의
│   │   └── IMPLEMENT_PLAN.md      # 구현 계획 지침
│   └── usage/
│       ├── quickstart.md          # 빠른 시작 가이드
│       └── commands.md            # CLI 커맨드 레퍼런스
│
├── CLAUDE.md
├── AGENTS.md
└── README.md
```

**핵심 포인트:**
- `skills/fragments/`: Claude Code와 Gemini CLI 양쪽 skill에서 공통으로 참조하는 지침 조각. 중복 방지.
- `cli/templates/`: Python `string.Template` 또는 단순 문자열 포매팅으로 처리. 외부 의존성 없음.
- `hooks/`: Claude Code 전용. Gemini CLI는 skill 지침에서 Agent에게 직접 기록 요청.

---

## 5. Remaining Design Sections / 남은 설계 항목

아래 항목들은 순차적으로 설계 및 검증 예정:

- [x] SQLite DB 스키마 설계 (tasks, operations, resources, settings 테이블)
- [x] Python CLI 서브커맨드 상세 설계
- [x] Skill 문서 구조 및 Agent 지침 설계
- [x] Hook 동작 명세
- [x] TODO.md / TASK_OPERATIONS.md 포맷 정의
- [x] Workflow 표현 방식 상세
- [x] Objective 데이터 모델
- [x] Resource 관리 상세
- [x] SETTINGS.md 구조
- [x] 초기화 프로세스 플로우

---

## 6. SQLite DB Schema / 데이터베이스 스키마

### 6.1 tasks 테이블

모든 ETS 컴포넌트(Project, Epic, Task, SubTask, Objective)를 저장하는 단일 테이블.

```sql
CREATE TABLE tasks (
    id          TEXT PRIMARY KEY,          -- Task ID (예: TOS-E001, TOS-T001)
    project_id  TEXT NOT NULL,             -- 프로젝트 ID (예: TOS)
    type        TEXT NOT NULL,             -- 'project' | 'epic' | 'task' | 'objective'
    title       TEXT NOT NULL,             -- 컴포넌트 제목
    description TEXT,                      -- 부가 설명
    status      TEXT NOT NULL DEFAULT 'todo',
                                           -- 'todo' | 'in_progress' | 'interrupted' | 'done' | 'cancelled'
    parent_id   TEXT,                      -- 상위 컴포넌트 ID (Epic→Project, Task→Epic, SubTask→Task)
    todo        TEXT,                      -- 세부 구현 계획 (markdown 텍스트)
    interrupt   TEXT,                      -- 중단 사유 (status가 interrupted일 때)

    -- Objective 전용 필드
    milestone_target TEXT,                 -- 마일스톤 달성 조건 (예: "MVP 완성")
    due_date    TEXT,                      -- 날짜 기반 이벤트 (ISO 8601: 2026-03-20)

    -- Workflow 관련
    seq_order   INTEGER,                   -- 실행 순서 (순차 정렬용)
    parallel_group TEXT,                   -- 병렬 그룹명 (같은 그룹은 동시 실행 가능)
    depends_on  TEXT,                      -- 선행 Task ID 목록 (JSON 배열: ["TOS-T001","TOS-T002"])

    -- 메타데이터
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

- `type='task'`인 레코드가 Task와 SubTask 모두 표현. `parent_id`가 Epic이면 Task, Task이면 SubTask.
- Objective는 `type='objective'`로 구분. `milestone_target`/`due_date`는 Objective 전용 (NULL 허용).
- `depends_on`은 JSON 배열 문자열. SQLite `json_each()`로 쿼리 가능.
- `parallel_group`이 같은 Task들은 동시 실행 가능한 그룹.

### 6.2 operations 테이블

AI Agent의 작업 처리 이력을 기록.

```sql
CREATE TABLE operations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT NOT NULL,              -- 작업 대상 Task ID
    operation_type  TEXT NOT NULL,              -- 'start' | 'progress' | 'complete' | 'error' | 'interrupt'
    agent_platform  TEXT,                       -- 'claude_code' | 'gemini_cli' | 기타
    summary         TEXT,                       -- 진행상황 요약 또는 결과 요약
    details         TEXT,                       -- 상세 내용 (JSON)
    subagent_used   INTEGER DEFAULT 0,          -- sub agent 사용 여부 (0/1)
    subagent_result TEXT,                       -- sub agent 사용 결과
    started_at      TEXT,                       -- 작업 시작 시간
    completed_at    TEXT,                       -- 작업 완료 시간
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

- 하나의 Task에 여러 operation 레코드 생성 가능 (시작 → 진행1 → 진행2 → 완료).
- `details`는 JSON 문자열 (도구 사용 내역, 편집 파일 목록 등).

### 6.3 resources 테이블

리소스 파일의 경로와 메타데이터 저장.

```sql
CREATE TABLE resources (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     TEXT NOT NULL,              -- 연관된 Task ID
    file_path   TEXT NOT NULL,              -- 파일 경로
    description TEXT,                       -- 리소스 설명
    res_type    TEXT NOT NULL DEFAULT 'reference',
                                           -- 'input' | 'output' | 'reference' | 'intermediate'
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

- `res_type`: `input`(시작 시 전달), `output`(결과물), `reference`(참조 문서), `intermediate`(중간 결과물 — `resources/` 폴더).

### 6.4 settings 테이블

프로젝트 설정 저장.

```sql
CREATE TABLE settings (
    key         TEXT PRIMARY KEY,           -- 설정 키
    value       TEXT NOT NULL,              -- 설정 값
    description TEXT,                       -- 설정 설명
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### 6.5 인덱스

```sql
CREATE INDEX idx_tasks_project    ON tasks(project_id);
CREATE INDEX idx_tasks_parent     ON tasks(parent_id);
CREATE INDEX idx_tasks_type       ON tasks(type);
CREATE INDEX idx_tasks_status     ON tasks(status);
CREATE INDEX idx_operations_task  ON operations(task_id);
CREATE INDEX idx_resources_task   ON resources(task_id);
```

---

## 7. Python CLI Commands / CLI 서브커맨드 상세 설계

진입점: `python cli/taskops.py <command> <subcommand> [options]`

### 7.1 `init` — 프로젝트 초기화

```bash
python taskops.py init --name "My Project" --prefix TOS --path ./my-project
# 결과: 지정 경로에 폴더 + SQLite DB + TODO.md + AGENTS.md + SETTINGS.md + resources/
```

### 7.2 `epic` — Epic 관리

```bash
python taskops.py epic create --title "인증 시스템 구현" --description "..."
python taskops.py epic list
python taskops.py epic show TOS-E001
python taskops.py epic update TOS-E001 --status done
python taskops.py epic delete TOS-E001
```

### 7.3 `task` — Task/SubTask 관리

```bash
# Task 생성 (Epic 하위)
python taskops.py task create --parent TOS-E001 --title "로그인 API 구현" --todo "- [ ] 엔드포인트 설계"
# SubTask 생성 (Task 하위 — 동일 커맨드)
python taskops.py task create --parent TOS-T001 --title "JWT 토큰 생성"

python taskops.py task list [--epic TOS-E001] [--status todo]
python taskops.py task show TOS-T001
python taskops.py task update TOS-T001 --status in_progress
python taskops.py task update TOS-T001 --status interrupted --interrupt "API 키 필요"
python taskops.py task delete TOS-T001
```

### 7.4 `objective` — Objective 관리

```bash
python taskops.py objective create --title "MVP 완성" --milestone "핵심 기능 3개 완료"
python taskops.py objective create --title "데모 발표" --due-date 2026-03-20
python taskops.py objective list
python taskops.py objective update OBJ-001 --status done
```

### 7.5 `workflow` — Workflow 관리

```bash
python taskops.py workflow set-order TOS-T001 TOS-T002 TOS-T003
python taskops.py workflow set-parallel --group "auth-group" TOS-T002 TOS-T003
python taskops.py workflow add-dep TOS-T003 --depends-on TOS-T001 TOS-T002
python taskops.py workflow show
python taskops.py workflow next    # 다음 실행 가능한 Task 조회
```

### 7.6 `op` — Operations 기록

```bash
python taskops.py op start TOS-T001 --platform claude_code
python taskops.py op progress TOS-T001 --summary "엔드포인트 3개 중 2개 완료"
python taskops.py op complete TOS-T001 --summary "로그인 API 구현 완료" --details '{"files":["auth.py"]}'
python taskops.py op log [--task TOS-T001]
```

### 7.7 `resource` — Resource 관리

```bash
python taskops.py resource add TOS-T001 --path ./docs/spec.md --type input --desc "API 스펙 문서"
python taskops.py resource list [--task TOS-T001]
```

### 7.8 `query` — 상태 조회/리포트

```bash
python taskops.py query status              # 프로젝트 전체 상태 요약
python taskops.py query tasks --status in_progress
python taskops.py query generate-todo       # TODO.md 재생성
python taskops.py query generate-ops        # TASK_OPERATIONS.md 재생성
```

### 7.9 `setting` — 설정 관리

```bash
python taskops.py setting set commit_style "conventional" --desc "커밋 메시지 스타일"
python taskops.py setting get commit_style
python taskops.py setting list
python taskops.py setting delete commit_style
```

---

## 8. Skill Document Structure / Skill 문서 구조 및 Agent 지침 설계

### 8.1 `skills/taskops.md` (Claude Code용)

```markdown
---
name: taskops
description: Project management skill using ETS structure (프로젝트를 ETS 구조로 관리)
---

## When to Use / 사용 시점
## Prerequisites / 사전 조건
## Phase 1: Initialization / 초기화
## Phase 2: Planning / 기획 (references fragments/ets-planning.md)
## Phase 3: Management / 관리
## Phase 4: Execution / 실행 (references fragments/monitoring-guide.md)
## Hook Integration / Hook 연동
```

### 8.2 `skills/taskops-gemini.md` (Gemini CLI용)

동일한 4단계 구조. 차이점:
- Hook 대신 Skill 지침으로 Agent에게 직접 기록 요청
- Gemini CLI 도구 이름 매핑 포함 (예: Claude `Bash` → Gemini `shell`)

### 8.3 `skills/fragments/` 공통 지침 조각

| 파일 | 내용 |
|------|------|
| `ets-planning.md` | ETS 구조 생성 규칙, ID 체계, 계층 구조 규칙 |
| `workflow-guide.md` | 순차/병렬 workflow 정의 방법, 의존성 설정 규칙 |
| `monitoring-guide.md` | operations 기록 시점, 기록할 내용, 포맷 |

### 8.4 Agent 핵심 지침 요약

1. **초기화 시**: `taskops.py init` → DB/파일 생성 → Hook 등록(Claude Code만)
2. **ETS 생성 시**: 요청 분석 → Epic → Task 분해 → workflow → TODO.md
3. **실행 시**: `workflow next` → `op start` → 작업 → `op progress` → `op complete` → `task update --status done`
4. **중단 시**: `task update --status interrupted --interrupt "사유"` → `op interrupt`
5. **조회 시**: `query status`, `query generate-todo`

---

## 9. Hook Specification / Hook 동작 명세

### 9.1 Hook 등록 위치

프로젝트 초기화 시 `.claude/settings.json`(프로젝트 레벨)에 등록.

### 9.2 Hook 목록

| Hook 파일 | 트리거 시점 | Hook 타입 | 동작 |
|-----------|------------|-----------|------|
| `on_task_start.sh` | Task 작업 시작 선언 시 | `PreToolUse` (Bash) | `op start` + status → `in_progress` |
| `on_tool_use.sh` | 주요 도구 사용 시 (Edit, Write, Bash) | `PostToolUse` | `op progress` — 도구/파일 기록 |
| `on_task_complete.sh` | Task 완료 선언 시 | `PostToolUse` (Bash) | `op complete` + status → `done` + TODO.md 재생성 |

### 9.3 Hook 동작 상세

**`on_task_start.sh`**
```bash
#!/bin/bash
TASK_ID="$1"
python cli/taskops.py task update "$TASK_ID" --status in_progress
```

**`on_tool_use.sh`**
```bash
#!/bin/bash
ACTIVE_TASK=$(python cli/taskops.py workflow current)
if [ -n "$ACTIVE_TASK" ]; then
    python cli/taskops.py op progress "$ACTIVE_TASK" \
        --summary "Tool used: $TOOL_NAME on $FILE_PATH"
fi
```

**`on_task_complete.sh`**
```bash
#!/bin/bash
TASK_ID="$1"
python cli/taskops.py task update "$TASK_ID" --status done
python cli/taskops.py query generate-todo
```

### 9.4 Hook 등록 설정

`.claude/settings.json`에 자동 추가:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|Bash",
        "command": "bash hooks/on_tool_use.sh"
      }
    ]
  }
}
```

### 9.5 Gemini CLI 대응

Hook 미지원. Skill 지침에서 Agent에게 명시적으로 CLI 호출을 요청:
- 작업 시작 전: `python taskops.py op start {TASK_ID}`
- 주요 단계 완료 시: `python taskops.py op progress {TASK_ID} --summary "..."`
- 작업 완료 시: `python taskops.py op complete {TASK_ID}`

---

## 10. TODO.md / TASK_OPERATIONS.md Format / 포맷 정의

### 10.1 TODO.md 포맷

```markdown
# My Project (TOS)

> Generated by TaskOps | Last updated: 2026-03-15 14:30:00

## Workflow / 실행 순서

1. TOS-T001: 로그인 API 구현
2. TOS-T002: 회원가입 API 구현
3. [parallel-group: auth-group]
   - TOS-T003: JWT 토큰 검증
   - TOS-T004: 세션 관리
4. TOS-T005: 통합 테스트

## Epic: 인증 시스템 구현 (TOS-E001) [In progress]

- [x] **TOS-T001**: 로그인 API 구현 `done`
  - 로그인 엔드포인트 설계 및 구현
  - [x] TOS-T006: DB 스키마 작성 `done`
  - [x] TOS-T007: 엔드포인트 구현 `done`
- [ ] **TOS-T002**: 회원가입 API 구현 `in_progress`
  - 회원가입 폼 검증 및 저장
  - [ ] TOS-T008: 입력값 검증 `todo`
- [ ] **TOS-T003**: JWT 토큰 검증 `todo`
- [ ] **TOS-T004**: 세션 관리 `todo`

## Epic: 대시보드 구현 (TOS-E002) [To do]

- [ ] **TOS-T005**: 통합 테스트 `todo`

## Objectives / 목표

- [ ] **MVP 완성** — 핵심 기능 3개 완료
- [ ] **데모 발표** — 2026-03-20
```

포맷 규칙:
- Workflow: 순서 번호 리스트. 병렬 그룹은 `[parallel-group: name]` 하위에 `-` 리스트.
- ETS 상세: Epic별 그룹핑, 체크박스 + Task ID + 제목 + 상태 백틱.
- SubTask: 부모 Task 아래 들여쓰기.
- Objective: 별도 섹션에 체크박스 + 마일스톤/날짜.

### 10.2 TASK_OPERATIONS.md 포맷

```markdown
# Task Operations Log

> Generated by TaskOps | Last updated: 2026-03-15 14:30:00

## TOS-T001: 로그인 API 구현

| # | Type | Platform | Time | Summary |
|---|------|----------|------|---------|
| 1 | start | claude_code | 2026-03-15 10:00 | — |
| 2 | progress | claude_code | 2026-03-15 10:15 | DB 스키마 작성 완료 |
| 3 | progress | claude_code | 2026-03-15 10:45 | 엔드포인트 3개 중 2개 완료 |
| 4 | complete | claude_code | 2026-03-15 11:00 | 로그인 API 구현 완료 |

## TOS-T002: 회원가입 API 구현

| # | Type | Platform | Time | Summary |
|---|------|----------|------|---------|
| 5 | start | claude_code | 2026-03-15 11:05 | — |
| 6 | progress | claude_code | 2026-03-15 11:20 | 입력값 검증 로직 작성 중 |
```

포맷 규칙:
- Task ID별 섹션 분리, 테이블로 시간순 기록.
- `query generate-ops` 커맨드로 DB에서 자동 생성.

---

## 11. Workflow Detail / Workflow 표현 방식 상세

### 11.1 Workflow 데이터 모델

별도 테이블 없이 `tasks` 테이블의 3개 필드로 표현:

| 필드 | 역할 | 예시 |
|------|------|------|
| `seq_order` | 전체 실행 순서 (정수) | `1`, `2`, `3` |
| `parallel_group` | 동시 실행 그룹명 (NULL이면 순차) | `NULL`, `"auth-group"` |
| `depends_on` | 선행 Task ID (JSON 배열) | `'["TOS-T001"]'` |

### 11.2 실행 순서 결정 로직

```
1. seq_order로 정렬
2. 같은 seq_order + 같은 parallel_group → 동시 실행 가능
3. depends_on의 Task가 모두 done → 실행 가능
4. 위 조건 충족 + status=todo → workflow next 결과
```

예시:
```
seq_order=1  TOS-T001 (group=NULL)           → 단독 실행
seq_order=2  TOS-T002 (group="auth-group")   → T001 완료 후
seq_order=2  TOS-T003 (group="auth-group")   → T002와 동시 실행 가능
seq_order=3  TOS-T004 (group=NULL, depends_on=["TOS-T002","TOS-T003"])
                                              → T002, T003 모두 완료 후
```

### 11.3 `workflow next` 쿼리 로직

```sql
SELECT id, title FROM tasks
WHERE status = 'todo'
  AND type = 'task'
  AND (
    depends_on IS NULL
    OR NOT EXISTS (
      SELECT 1 FROM json_each(depends_on) AS dep
      JOIN tasks AS t ON t.id = dep.value
      WHERE t.status != 'done'
    )
  )
ORDER BY seq_order ASC;
```

### 11.4 CLI 동작

```bash
# 순서 설정: 각 Task에 seq_order = 1, 2, 3, ... 부여
python taskops.py workflow set-order TOS-T001 TOS-T002 TOS-T003

# 병렬 그룹: 같은 seq_order 내에서 동시 실행 가능으로 표시
python taskops.py workflow set-parallel --group "auth-group" TOS-T002 TOS-T003

# 의존성: depends_on JSON 배열에 추가
python taskops.py workflow add-dep TOS-T003 --depends-on TOS-T001 TOS-T002
```

---

## 12. Objective Data Model / Objective 데이터 모델

Objective는 `tasks` 테이블에 `type='objective'`로 저장.

| 속성 | 마일스톤 타입 | 날짜 이벤트 타입 |
|------|-------------|----------------|
| `type` | `'objective'` | `'objective'` |
| `title` | "MVP 완성" | "데모 발표" |
| `milestone_target` | "핵심 기능 3개 완료" | `NULL` |
| `due_date` | `NULL` | `"2026-03-20"` |
| `parent_id` | 프로젝트 ID (예: `TOS`) | 프로젝트 ID |
| `status` | `todo` → `done` | `todo` → `done` |

- **ID 체계**: `{PREFIX}-O001`, `{PREFIX}-O002`, ... (Objective 전용 시퀀스)
- **달성 판단**: 자동 판단 없음. Agent/사용자가 수동으로 `done` 변경. Skill에서 "관련 Task 완료 시 Objective 달성 여부 확인하라"고 가이드.

---

## 13. Resource Management Detail / Resource 관리 상세

| 경우 | 저장 위치 | DB 기록 |
|------|----------|---------|
| 사용자가 명시적으로 요청한 파일 | 사용자 지정 경로 | `resources` 테이블에 경로 참조 |
| Task 처리 중 중간 결과물 | `{project_path}/resources/{TASK_ID}_filename` | `res_type='intermediate'` |
| 작업 시작 시 전달 자료 | 원본 경로 | `res_type='input'` |
| 작업 결과물 | 사용자 지정 또는 프로젝트 내 | `res_type='output'` |

파일명 규칙: 중간 결과물은 `{TASK_ID}_{원본파일명}` 형태. 예: `TOS-T001_api_spec.md`

---

## 14. SETTINGS.md Structure / SETTINGS.md 구조

```markdown
# Project Settings

> AI Agent 행동 지침 / Agent Behavior Guidelines

## General / 일반

- autonomy_level: moderate
  # Agent 자율성 수준 (low | moderate | high)

- commit_style: conventional
  # 커밋 메시지 스타일

## Execution / 실행

- use_subagent: true
  # Sub Agent 사용 허용 여부

- parallel_execution: true
  # 병렬 그룹 Task 동시 실행 허용 여부

## Monitoring / 모니터링

- progress_interval: major_steps
  # 진행 기록 간격 (every_tool | major_steps | start_end_only)
```

DB 연동: SETTINGS.md와 `settings` 테이블 양쪽 동기화. CLI 변경 시 양쪽 모두 업데이트.

---

## 15. Initialization Flow / 초기화 프로세스 플로우

```
사용자: "프로젝트 만들어줘"
    │
    ▼
[1] python taskops.py init --name "Project Name" --prefix PRJ --path ./project-path
    ├── 프로젝트 폴더 생성: {path}/
    ├── 하위 폴더 생성: {path}/resources/
    ├── SQLite DB 생성: {path}/taskops.db
    │   └── tasks, operations, resources, settings 테이블 생성
    ├── TODO.md 생성 (빈 템플릿)
    ├── AGENTS.md 생성 (프로젝트 요약 정보)
    ├── SETTINGS.md 생성 (기본 설정)
    └── TASK_OPERATIONS.md 생성 (빈 템플릿)
    │
    ▼
[2] Hook 등록 (Claude Code만)
    ├── .claude/settings.json에 Hook 설정 추가
    └── hooks/ 스크립트 경로 등록
    │
    ▼
[3] settings 테이블에 기본 설정값 삽입
    │
    ▼
[4] tasks 테이블에 Project 레코드 생성
    │   id: "{PREFIX}", type: "project"
    │   title: "Project Name", status: "in_progress"
    │
    ▼
[완료] 초기화 완료 메시지 출력
```
