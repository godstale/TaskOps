# TaskOps Implementation TODO

> Status: Implementation In Progress
> Plan: `docs/plans/2026-03-15-taskops-implementation.md`
> Design: `docs/design/2026-03-15-taskops-design.md`

## Phase 1: Foundation / 기반 구축

- [x] **Task 1**: Project Scaffolding — 디렉토리 구조 생성
- [x] **Task 2**: DB Schema — SQLite 스키마 정의 (`cli/db/schema.py`)
  - [x] Unit Test: 테이블 생성 검증, 멱등성 검증 (`tests/unit/test_schema.py`) ✅ 5 passed
- [x] **Task 3**: DB Connection — DB 연결 관리 (`cli/db/connection.py`)
  - [x] Unit Test: 연결 생성, 자동 초기화 검증 (`tests/unit/test_connection.py`) ✅ 5 passed
- [x] **Task 4**: CLI Entry Point — argparse 진입점 (`cli/taskops.py`)
  - [x] Unit Test: help 출력, version 출력, 잘못된 커맨드 에러 (`tests/unit/test_cli.py`) ✅ 5 passed

## Phase 2: Core Commands / 핵심 커맨드

- [x] **Task 5**: `init` Command — 프로젝트 초기화
  - [x] Unit Test: 폴더/DB/템플릿 파일 생성 검증 (`tests/unit/test_cmd_init.py`) ✅ 6 passed
  - [x] Integration Test: init → DB 상태 확인 → 파일 내용 검증 (`tests/integration/test_init_flow.py`) ✅ 6 passed
- [x] **Task 6**: `epic` Command — Epic CRUD
  - [x] Unit Test: create/list/show/update/delete 각각 검증 (`tests/unit/test_cmd_epic.py`) ✅ 8 passed
- [x] **Task 7**: `task` Command — Task/SubTask CRUD
  - [x] Unit Test: create/list/show/update/delete, SubTask 계층 검증 (`tests/unit/test_cmd_task.py`) ✅ 12 passed
- [x] **Task 8**: `objective` Command — Objective CRUD
  - [x] Unit Test: 마일스톤/날짜 이벤트 생성, 상태 변경 (`tests/unit/test_cmd_objective.py`) ✅ 10 passed
- [x] **Task 9**: `workflow` Command — Workflow 관리
  - [x] Unit Test: set-order, set-parallel, add-dep, next, current (`tests/unit/test_cmd_workflow.py`) ✅ 13 passed
  - [x] Integration Test: 순차/병렬/의존성 시나리오별 next 결과 검증 (`tests/integration/test_workflow_flow.py`) ✅ 5 passed
- [x] **Task 10**: `op` Command — Operations 기록
  - [x] Unit Test: start/progress/complete/error/interrupt/log (`tests/unit/test_cmd_operation.py`) ✅ 11 passed
- [x] **Task 11**: `resource` Command — Resource 관리
  - [x] Unit Test: add/list, 타입별 필터링 (`tests/unit/test_cmd_resource.py`) ✅ 8 passed
- [x] **Task 12**: `query` Command — 상태 조회/리포트
  - [x] Unit Test: status 요약, tasks 필터링 (`tests/unit/test_cmd_query.py`) ✅ 9 passed
  - [x] Integration Test: generate-todo/generate-ops 결과 포맷 검증 (`tests/integration/test_query_generation.py`) ✅ 5 passed
- [x] **Task 13**: `setting` Command — 설정 관리
  - [x] Unit Test: set/get/list/delete, SETTINGS.md 동기화 (`tests/unit/test_cmd_setting.py`) ✅ 10 passed

## Phase 3: Integration / 통합

- [x] **Task 14**: Hook Scripts — Claude Code Hook 스크립트
  - [x] Integration Test: Hook 실행 → DB 상태 변경 검증 (`tests/integration/test_hooks.py`) ✅ 5 passed
- [x] **Task 15**: Skill Doc (Claude Code) — Claude Code 용 Skill 문서 (`skills/taskops.md` + `skills/fragments/`)
- [x] **Task 16**: Skill Doc (Gemini CLI) — Gemini CLI 용 Skill 문서 (`skills/taskops-gemini.md`)

## Phase 4: Finalization / 마무리

- [x] **Task 17**: Documentation — 사용 문서 작성
  - [x] `docs/usage/quickstart.md`, `docs/usage/commands.md`, `README.md`
- [x] **Task 18**: E2E Integration Test — 전체 라이프사이클 통합 테스트
  - [x] init → epic → task → subtask → objective → workflow → op → query 전체 흐름 (`tests/integration/test_e2e.py`) ✅ 1 passed
  - [x] Integration Test: init → DB 상태 확인 → 파일 내용 검증 (`tests/integration/test_init_flow.py`) ✅ 6 passed
  - [x] Integration Test: 순차/병렬/의존성 시나리오별 next 결과 검증 (`tests/integration/test_workflow_flow.py`) ✅ 5 passed
  - [x] Integration Test: generate-todo/generate-ops 결과 포맷 검증 (`tests/integration/test_query_generation.py`) ✅ 5 passed
- [x] **Task 19**: Final Review — 전체 테스트 실행 및 최종 검토 ✅ 124 passed (102 unit + 22 integration)

## Test Structure / 테스트 구조

```
tests/
├── __init__.py
├── conftest.py              # 공통 fixture (임시 DB, 임시 프로젝트 폴더)
├── unit/                    # 유닛 테스트 — 개별 모듈/함수 단위
│   ├── __init__.py
│   ├── test_schema.py
│   ├── test_connection.py
│   ├── test_cli.py
│   ├── test_cmd_init.py
│   ├── test_cmd_epic.py
│   ├── test_cmd_task.py
│   ├── test_cmd_objective.py
│   ├── test_cmd_workflow.py
│   ├── test_cmd_operation.py
│   ├── test_cmd_resource.py
│   ├── test_cmd_query.py
│   └── test_cmd_setting.py
└── integration/             # 통합 테스트 — 여러 커맨드 조합 시나리오
    ├── __init__.py
    ├── test_init_flow.py
    ├── test_workflow_flow.py
    ├── test_query_generation.py
    ├── test_hooks.py
    └── test_e2e.py
```

## Test Guidelines / 테스트 지침

- **TDD**: 각 커맨드 구현 전에 테스트를 먼저 작성
- **Fixture**: `conftest.py`에 임시 DB와 초기화된 프로젝트 폴더 fixture 제공
- **격리**: 각 테스트는 독립된 임시 디렉토리에서 실행 (side effect 없음)
- **실행**: `python -m pytest tests/unit/ -v` (유닛), `python -m pytest tests/integration/ -v` (통합)
- **전체**: `python -m pytest tests/ -v` (전체 테스트)
