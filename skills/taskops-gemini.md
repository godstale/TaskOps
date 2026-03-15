---
name: taskops-gemini
description: Manage complex projects using ETS (Epic-Task-SubTask) structure with SQLite-backed tracking. Gemini CLI version with explicit operation recording.
---

# TaskOps — Project Management Skill for Gemini CLI

## When to Use / 사용 시점

Use TaskOps when managing a project that involves multiple tasks, dependencies, or tracking progress across sessions. Ideal for:
- Multi-step implementation projects
- Projects requiring structured decomposition
- Work that spans multiple sessions and needs progress tracking

## Prerequisites / 사전 조건

- Python 3.10+
- TaskOps repository cloned (contains `cli/` package)
- Project initialized with `python -m cli init`

> **Note for Gemini CLI:** Gemini CLI does not support hooks. You MUST explicitly call operation recording commands at each step. This is the key difference from the Claude Code version.

---

## Phase 1: Initialization / 초기화

Initialize a new TaskOps project in the target directory.

```bash
python -m cli init --name "Project Name" --prefix PRJ --path ./project-path
```

This creates:
- `taskops.db` — SQLite database
- `TODO.md` — Auto-generated task overview
- `AGENTS.md` — Agent instructions
- `SETTINGS.md` — Project settings
- `resources/` — Resource file directory

---

## Phase 2: Planning / 기획

Decompose the project into ETS components.

### ETS Hierarchy / ETS 계층

```
Project
  └── Epic — Major feature unit (에픽)
        └── Task — Implementation unit (태스크)
              └── SubTask — Detailed step (서브태스크)
  └── Objective — Milestone or deadline (목표)
```

### Create Structure / 구조 생성

```bash
# Create Epics (대규모 기능 단위)
python -m cli epic create --title "Authentication System"

# Create Tasks under Epic (구현 단위)
python -m cli task create --parent PRJ-E001 --title "Login API"

# Create SubTasks under Task (세부 작업, 필요한 경우만)
python -m cli task create --parent PRJ-T001 --title "JWT token generation"

# Create Objectives (마일스톤/일정 목표)
python -m cli objective create --title "MVP Complete" --milestone "Core features done"
python -m cli objective create --title "Demo Day" --due-date 2026-04-01
```

### Define Workflow / Workflow 정의

```bash
# Set execution order (실행 순서 설정)
python -m cli workflow set-order PRJ-T001 PRJ-T002 PRJ-T003

# Group tasks for parallel execution (병렬 그룹 설정)
python -m cli workflow set-parallel --group "auth-group" PRJ-T002 PRJ-T003

# Add dependencies (의존성 추가)
python -m cli workflow add-dep PRJ-T004 --depends-on PRJ-T002 PRJ-T003
```

### Generate TODO.md / TODO.md 생성

```bash
python -m cli query generate-todo
```

---

## Phase 3: Execution / 실행

Work through tasks following the workflow order.

> **IMPORTANT / 중요:** Since Gemini CLI has no hooks, you MUST manually call the operation recording commands at each step.

### Start a Task / 작업 시작

```bash
# Check next executable task (다음 실행 가능 태스크 확인)
python -m cli workflow next

# REQUIRED: Update status and record start (상태 업데이트 및 시작 기록 — 필수)
python -m cli task update PRJ-T001 --status in_progress
python -m cli op start PRJ-T001 --platform gemini_cli
```

### Record Progress / 진행 기록

After completing meaningful milestones during implementation:

```bash
# REQUIRED: Record progress with descriptive summary (진행 기록 — 필수)
python -m cli op progress PRJ-T001 --summary "Implemented 3 of 5 endpoints"
```

Record progress at these points:
- After implementing a major component
- After writing or passing tests
- After resolving a significant issue
- Before switching to a different task

### Complete a Task / 작업 완료

```bash
# REQUIRED: Mark done, record completion, regenerate TODO (완료 처리 — 필수)
python -m cli task update PRJ-T001 --status done
python -m cli op complete PRJ-T001 --summary "Login API complete, all tests pass"
python -m cli query generate-todo
```

### Handle Interruptions / 중단 처리

```bash
python -m cli task update PRJ-T001 --status interrupted --interrupt "Waiting for API key"
python -m cli op interrupt PRJ-T001 --summary "Blocked on external dependency"
```

### Handle Errors / 오류 처리

```bash
python -m cli op error PRJ-T001 --summary "Database connection failed"
```

---

## Phase 4: Monitoring / 모니터링

### Check Project Status / 프로젝트 상태 확인

```bash
# Overall status with progress percentage (전체 상태 요약)
python -m cli query status

# List tasks by status (상태별 태스크 조회)
python -m cli query tasks --status in_progress

# View operation log for a task (작업 로그 조회)
python -m cli op log --task PRJ-T001

# View full workflow (전체 워크플로우 조회)
python -m cli workflow show
```

### Regenerate Reports / 리포트 재생성

```bash
python -m cli query generate-todo
python -m cli query generate-ops
```

### Manage Resources / 리소스 관리

```bash
python -m cli resource add PRJ-T001 --path ./docs/spec.md --type input --desc "API spec"
python -m cli resource list --task PRJ-T001
```

### Manage Settings / 설정 관리

```bash
python -m cli setting set commit_style "conventional" --desc "Commit message style"
python -m cli setting get commit_style
python -m cli setting list
```

---

## Gemini CLI Tool Mapping / Gemini CLI 도구 매핑

| Claude Code Tool | Gemini CLI Equivalent |
|-----------------|----------------------|
| `Edit` | `edit_file` |
| `Write` | `write_file` |
| `Read` | `read_file` |
| `Bash` | `run_shell` |
| `Glob` | `list_files` |
| `Grep` | `search_files` |

---

## Reference: All CLI Commands / CLI 명령어 전체 참조

| Command | Description |
|---------|-------------|
| `init --name --prefix --path` | Initialize project |
| `epic create/list/show/update/delete` | Epic CRUD |
| `task create/list/show/update/delete` | Task/SubTask CRUD |
| `objective create/list/update/delete` | Objective CRUD |
| `workflow set-order/set-parallel/add-dep/show/next/current` | Workflow management |
| `op start/progress/complete/error/interrupt/log` | Operations recording |
| `resource add/list` | Resource management |
| `query status/tasks/generate-todo/generate-ops` | Status queries and reports |
| `setting set/get/list/delete` | Settings management |

All commands use: `python -m cli [--db path] <command> <subcommand> [options]`

---

## Visualizing with TaskBoard / 시각화 도구 TaskBoard

TaskBoard는 TaskOps DB를 읽기 전용으로 시각화하는 별도 도구입니다.
사용자가 프로젝트 진행 상황을 GUI로 보고 싶을 때 설치를 안내하세요.

**설치 (Install)**

```bash
git clone https://github.com/godstale/TaskBoard.git
cd TaskBoard
pnpm install
```

**실행 (Run)**

```bash
# TUI (터미널)
pnpm --filter @taskboard/tui dev -- --path /path/to/taskops-root

# Electron (데스크탑 앱)
pnpm --filter @taskboard/electron dev
```

TaskBoard는 TaskOps가 생성한 `taskops.db`를 자동으로 감시하며, DB 변경 시 화면을 자동으로 갱신합니다.
→ [TaskBoard GitHub](https://github.com/godstale/TaskBoard)
