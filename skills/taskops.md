---
name: taskops
description: Manage complex projects using ETS (Epic-Task-SubTask) structure with SQLite-backed tracking, workflow management, and operations monitoring.
---

# TaskOps — Project Management Skill for Claude Code

## When to Use / 사용 시점

Use TaskOps when managing a project that involves multiple tasks, dependencies, or tracking progress across sessions. Ideal for:
- Multi-step implementation projects
- Projects requiring structured decomposition
- Work that spans multiple sessions and needs progress tracking

## Prerequisites / 사전 조건

- Python 3.10+
- TaskOps repository cloned (contains `cli/` package and `hooks/`)
- Project initialized with `python -m cli init`

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

### Configure Hooks / Hook 설정

Register TaskOps hooks in `.claude/settings.json` (project-level):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|Bash",
        "command": "bash /path/to/TaskOps/hooks/on_tool_use.sh"
      }
    ]
  }
}
```

Available hooks:
- `on_task_start.sh <TASK_ID>` — Sets task to `in_progress`, records `op start`
- `on_tool_use.sh` — Records `op progress` for the current active task
- `on_task_complete.sh <TASK_ID>` — Sets task to `done`, records `op complete`, regenerates TODO.md

---

## Phase 2: Planning / 기획

Decompose the project into ETS components. Follow the ETS Planning Guide below.

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

### Start a Task / 작업 시작

```bash
# Check next executable task (다음 실행 가능 태스크 확인)
python -m cli workflow next

# Start the task (작업 시작 기록)
python -m cli task update PRJ-T001 --status in_progress
python -m cli op start PRJ-T001 --platform claude_code
```

If hooks are configured, use `bash hooks/on_task_start.sh PRJ-T001` instead.

### Record Progress / 진행 기록

```bash
# Record meaningful progress milestones (의미있는 진행 단계 기록)
python -m cli op progress PRJ-T001 --summary "Implemented 3 of 5 endpoints"
```

With hooks configured, `on_tool_use.sh` records progress automatically on each tool use.

### Complete a Task / 작업 완료

```bash
# Mark task as done (완료 처리)
python -m cli task update PRJ-T001 --status done
python -m cli op complete PRJ-T001 --summary "Login API complete, all tests pass"
python -m cli query generate-todo
```

If hooks are configured, use `bash hooks/on_task_complete.sh PRJ-T001` instead.

### Handle Interruptions / 중단 처리

```bash
# Record interruption with reason (중단 사유 기록)
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
# Regenerate TODO.md (TODO.md 재생성)
python -m cli query generate-todo

# Generate operations report (작업 기록 리포트)
python -m cli query generate-ops
```

### Manage Resources / 리소스 관리

```bash
# Add resource reference to a task (태스크에 리소스 연결)
python -m cli resource add PRJ-T001 --path ./docs/spec.md --type input --desc "API spec"

# List resources (리소스 목록 조회)
python -m cli resource list --task PRJ-T001
```

### Manage Settings / 설정 관리

```bash
python -m cli setting set commit_style "conventional" --desc "Commit message style"
python -m cli setting get commit_style
python -m cli setting list
```

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
