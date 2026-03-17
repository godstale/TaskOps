# TaskOps

**AI Agent 프로젝트 관리 Skill** — ETS (Epic-Task-SubTask) 구조로 복잡한 프로젝트를 분해하고, SQLite 기반 추적·워크플로우 관리·작업 이력 기록을 제공합니다.

**Claude Code** (hooks 지원)와 **Gemini CLI** (명시적 기록 방식)를 모두 지원합니다.

> English docs: [README.md](README.md)

---

## 주요 기능

TaskOps는 AI Agent가 세션을 넘어 멀티스텝 프로젝트를 체계적으로 관리할 수 있도록 합니다.

- **ETS 계층 구조**: 프로젝트를 Epic → Task → SubTask로 분해
- **워크플로우 엔진**: 순차/병렬 실행 및 의존성 추적
- **작업 이력 기록**: 태스크별 start/progress/complete/error/interrupt 이벤트 기록
- **자동 리포트**: DB 상태에서 `TODO.md`와 `TASK_OPERATIONS.md` 자동 생성
- **리소스 연결**: 파일/URL을 태스크에 연결
- **설정 저장소**: `SETTINGS.md`와 동기화되는 key-value 설정
- **시각화 모니터링**: [TaskBoard](https://github.com/godstale/TaskBoard)로 실시간 진행 상황 확인 (TUI 또는 Electron 데스크탑 앱)

## 빠른 시작

```bash
git clone https://github.com/godstale/TaskOps.git
cd my-project

# 프로젝트에 TaskOps 초기화
python -m cli init --name "My Project" --prefix MYP --path .

# 계획: Epic과 Task 생성
python -m cli epic create --title "Core Feature"
python -m cli task create --parent MYP-E001 --title "Implement API"

# 워크플로우 순서 설정
python -m cli workflow set-order MYP-T001
python -m cli query generate-todo

# 실행
python -m cli workflow next          # -> MYP-T001
python -m cli task update MYP-T001 --status in_progress
python -m cli op start MYP-T001 --platform claude_code
# ... 작업 수행 ...
python -m cli task update MYP-T001 --status done
python -m cli op complete MYP-T001 --summary "API 구현 완료"
python -m cli query generate-todo
```

전체 가이드: [docs/usage/quickstart.md](docs/usage/quickstart.md)

## TaskBoard로 모니터링

[TaskBoard](https://github.com/godstale/TaskBoard)는 TaskOps SQLite DB를 실시간으로 읽어 프로젝트 상태를 시각화하는 도구입니다. **터미널 UI (TUI)** 또는 **Electron 데스크탑 앱** 형태로 실행되며, DB 변경 시 자동으로 화면을 갱신합니다.

```bash
git clone https://github.com/godstale/TaskBoard.git
cd TaskBoard
pnpm install

# TUI (터미널)
pnpm --filter @taskboard/tui dev -- --path /path/to/your-project

# Electron (데스크탑)
pnpm --filter @taskboard/electron dev
```

TaskBoard는 읽기 전용으로 동작하며 TaskOps DB에 쓰기 작업을 하지 않습니다. AI Agent가 작업을 진행하는 동안 진행 상황을 실시간으로 모니터링할 때 사용하세요.

---

## Skill로 사용하기

### Claude Code

`npx skills add godstale/TaskOps`로 설치하거나, `SKILL.md`를 skills 디렉토리에 수동으로 복사합니다.

이 skill은 **자동 호출**되도록 설계되어 있습니다 — 계획이 확정되고 실행이 시작되려 할 때, 사용자의 명시적 지시 없이도 AI Agent가 TaskOps를 자동으로 호출합니다.

작업 이력을 자동 기록하려면 `.claude/settings.json`에 hooks를 설정하세요:

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

### Gemini CLI

`skills/taskops-gemini.md`를 사용합니다. Gemini CLI는 hooks를 지원하지 않으므로, skill이 각 단계마다 `op` 명령어를 명시적으로 호출하도록 안내합니다.

## 프로젝트 구조

```
TaskOps/
├── SKILL.md                 # 루트 skill 파일 (npx skills add 용)
├── cli/                     # Python CLI 패키지
│   ├── __main__.py          # 진입점: python -m cli
│   ├── taskops.py           # argparse 라우팅
│   ├── db/                  # DB 레이어 (schema, connection)
│   ├── commands/            # 서브커맨드 모듈
│   └── templates/           # MD 파일 템플릿
├── hooks/                   # Claude Code hook 스크립트
│   ├── on_task_start.sh
│   ├── on_task_complete.sh
│   └── on_tool_use.sh
├── skills/                  # AI Agent skill 문서
│   ├── taskops.md           # Claude Code skill
│   ├── taskops-gemini.md    # Gemini CLI skill
│   └── fragments/           # 공유 instruction fragments
├── tests/                   # 테스트
│   ├── unit/                # 유닛 테스트
│   └── integration/         # 통합 테스트
└── docs/usage/              # 문서
```

## CLI 명령어 참조

전체 명령어 참조: [docs/usage/commands.md](docs/usage/commands.md)

| 커맨드 | 설명 |
|--------|------|
| `init --name --prefix --path` | 프로젝트 초기화 |
| `epic create/list/show/update/delete` | Epic CRUD |
| `task create/list/show/update/delete` | Task/SubTask CRUD |
| `objective create/list/update/delete` | Objective CRUD |
| `workflow set-order/set-parallel/add-dep/show/next/current` | 워크플로우 관리 |
| `workflow restart <W-ID> [--clear-ops]` | 워크플로우 Task를 todo로 초기화하여 재실행 |
| `op start/progress/complete/error/interrupt/log` | 작업 이력 기록 |
| `resource add/list [--task/--workflow/--type]` | 리소스 관리 |
| `query status/tasks/generate-todo/generate-ops` | 상태 조회 및 리포트 |
| `setting set/get/list/delete` | 설정 관리 |

## 요구사항

- Python 3.10+
- 외부 의존성 없음 (표준 라이브러리만 사용: `sqlite3`, `argparse`, `json`, `string`)

## 테스트

```bash
# 유닛 테스트
python -m pytest tests/unit/ -v

# 통합 테스트 (bash 필요)
python -m pytest tests/integration/ -v

# 전체 테스트
python -m pytest tests/ -v
```
