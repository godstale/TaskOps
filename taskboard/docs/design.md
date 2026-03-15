# TaskBoard Design Document

> Date: 2026-03-15
> Status: Approved

---

## 1. Overview

TaskBoard는 TaskOps가 관리하는 프로젝트의 작업을 시각적으로 표현하는 도구입니다.
TUI(터미널)와 Electron(데스크탑) 두 가지 앱을 pnpm workspaces 모노레포로 구현합니다.
TaskOps DB(SQLite)를 읽기 전용으로 참조하며, DB 변경 시 자동으로 화면을 갱신합니다.

---

## 2. Design Decisions

| # | 항목 | 결정 |
|---|------|------|
| 1 | 모노레포 구조 | pnpm workspaces (`core`, `tui`, `electron`) |
| 2 | 코드 공유 | 비즈니스 로직은 `@taskboard/core`로 분리, UI 레이어만 각 앱에서 구현 |
| 3 | 기능 범위 | TUI와 Electron 동일 — 4개 화면 (Dashboard, Task Operations, Resources, Settings) |
| 4 | 데이터 접근 | 읽기 전용. 수정은 AI Agent가 CLI로만 수행 |
| 5 | 데이터 갱신 | chokidar 파일 감시 + 3초 폴링 fallback |
| 6 | 폴더 선택 | CLI 인자(`--path`) + 인터랙티브 fallback 혼합 |
| 7 | Dashboard (TUI) | 계층 리스트 + 상태 아이콘 + 진행률 바 |
| 8 | Dashboard (Electron) | frappe-gantt Gantt 차트 |
| 9 | Task Operations Flow | ReactFlow 노드-엣지 다이어그램 (Electron) / 텍스트 플로우 (TUI) |
| 10 | Task 계층 표시 | 상단 바 `부모 > 현재 ▼`, 클릭 시 팝업으로 계층 구조 표시 |
| 11 | 배포 위치 | `taskops/taskboard/` |
| 12 | 테스트 | Vitest (unit/component), Playwright E2E (Electron) |

---

## 3. Repository Structure

```
taskops/
└── taskboard/
    ├── package.json                    # pnpm workspaces root
    ├── pnpm-workspace.yaml
    ├── packages/
    │   ├── core/                       # 공통 비즈니스 로직
    │   │   ├── src/
    │   │   │   ├── db.ts               # better-sqlite3 연결
    │   │   │   ├── models.ts           # 타입 정의
    │   │   │   ├── queries.ts          # 데이터 조회 함수
    │   │   │   └── watcher.ts          # DB 파일 감시
    │   │   ├── tests/
    │   │   └── package.json
    │   │
    │   ├── tui/                        # 터미널 TUI 앱
    │   │   ├── src/
    │   │   │   ├── index.tsx           # 진입점 (CLI 인자 파싱)
    │   │   │   ├── App.tsx             # 루트 컴포넌트 (화면 라우팅)
    │   │   │   └── screens/
    │   │   │       ├── ProjectSelect.tsx
    │   │   │       ├── Dashboard.tsx
    │   │   │       ├── TaskOperations.tsx
    │   │   │       ├── Resources.tsx
    │   │   │       └── Settings.tsx
    │   │   ├── tests/
    │   │   └── package.json
    │   │
    │   └── electron/                   # Electron 앱
    │       ├── src/
    │       │   ├── main/
    │       │   │   └── index.ts        # Electron main process (IPC, watcher)
    │       │   └── renderer/
    │       │       ├── App.tsx         # 루트 컴포넌트
    │       │       └── screens/
    │       │           ├── ProjectSelect.tsx
    │       │           ├── Dashboard.tsx       # frappe-gantt
    │       │           ├── TaskOperations.tsx  # ReactFlow
    │       │           ├── Resources.tsx
    │       │           └── Settings.tsx
    │       ├── tests/
    │       └── package.json
    └── fixtures/
        └── fixture.db                  # 테스트용 샘플 DB
```

---

## 4. Tech Stack

| 레이어 | 기술 |
|--------|------|
| core | TypeScript, better-sqlite3, chokidar |
| TUI | Ink 5, ink-select-input |
| Electron UI | Electron 33, React 18, Vite, Tailwind CSS |
| Gantt (Electron) | frappe-gantt |
| Flow 다이어그램 (Electron) | ReactFlow |
| 테스트 | Vitest, ink-testing-library, React Testing Library, Playwright |

---

## 5. Core Package Design

### Data Models (`models.ts`)

```typescript
type TaskStatus = 'todo' | 'in_progress' | 'interrupted' | 'done' | 'cancelled'
type TaskType = 'project' | 'epic' | 'task' | 'objective'

interface Task {
  id: string
  project_id: string
  type: TaskType
  title: string
  description?: string
  status: TaskStatus
  parent_id?: string
  seq_order?: number
  parallel_group?: string
  depends_on?: string[]   // JSON 파싱 후
  milestone_target?: string
  due_date?: string
  created_at: string
  updated_at: string
}

interface Operation {
  id: number
  task_id: string
  operation_type: 'start' | 'progress' | 'complete' | 'error' | 'interrupt'
  agent_platform?: string
  summary?: string
  started_at?: string
  completed_at?: string
  created_at: string
}

interface Resource {
  id: number
  task_id: string
  file_path: string
  description?: string
  res_type: 'input' | 'output' | 'reference' | 'intermediate'
  created_at: string
}
```

### Query Functions (`queries.ts`)

| 함수 | 용도 |
|------|------|
| `getProject(db)` | 프로젝트 기본 정보 |
| `getEpicsWithTasks(db)` | Epic + 하위 Task/SubTask 계층 구조 |
| `getWorkflowOrder(db)` | seq_order 기준 정렬된 Task 목록 |
| `getOperations(db, taskId?)` | 전체 또는 특정 Task의 operation 이력 |
| `getResources(db, taskId?)` | 전체 또는 특정 Task의 리소스 목록 |
| `getSettings(db)` | 설정 전체 |
| `getProjectList(taskopsRoot)` | TaskOps 폴더 내 프로젝트 디렉토리 스캔 |

### DB Watcher (`watcher.ts`)

```
1. chokidar로 taskops.db 파일 감시 (fs.watch 기반)
2. 변경 감지 시 onChange 콜백 호출
3. chokidar 실패 시 setInterval(3000ms) 폴링으로 fallback
4. 인터페이스: watch(dbPath, onChange) => unwatch()
```

---

## 6. TUI App Design

### Screen Flow

```
실행: npx taskboard-tui [--path <taskops-root>]
      │
      ├─ --path 지정됨 → 프로젝트 선택 화면
      └─ --path 없음  → 폴더 경로 입력 → 프로젝트 선택 화면
                                  │
                            Dashboard (기본)
                          Tab 키로 화면 전환:
                Dashboard | TaskOps | Resources | Settings
```

### Dashboard Layout

```
┌─ MY PROJECT (TOS) ──────────────────────────────┐
│ Epics: 3  Tasks: 12  Done: 5/12  In Progress: 2  │
├──────────────────────────────────────────────────┤
│ [E001] 인증 시스템 구현          ▓▓▓▓░░░░ 50%     │
│   ✓ [T001] 로그인 API           done              │
│   ● [T002] 회원가입 API          in_progress       │
│   ○ [T003] JWT 검증              todo              │
│ [E002] 대시보드 구현             ░░░░░░░░ 0%       │
│   ○ [T004] 통합 테스트           todo              │
├──────────────────────────────────────────────────┤
│ [Tab] 화면전환  [R] 새로고침  [Q] 종료             │
└──────────────────────────────────────────────────┘
```

상태 아이콘: `✓` done, `●` in_progress, `○` todo, `✕` interrupted

### Task Operations Layout

```
┌─ TASK OPERATIONS ────────────────────────────────┐
│ [T001] 로그인 API  [T002] 회원가입 API  ...        │
│ (화살표로 Task 선택)                               │
├──────────────────────────────────────────────────┤
│ TOS-T001: 로그인 API 구현                          │
│ ────────────────────────────────                  │
│ ● start      10:00  claude_code                   │
│ │ progress   10:15  DB 스키마 작성 완료            │
│ │ progress   10:45  엔드포인트 2/3 완료            │
│ ✓ complete   11:00  로그인 API 구현 완료           │
└──────────────────────────────────────────────────┘
```

---

## 7. Electron App Design

### Screen Flow

```
실행: npx taskboard [--path <taskops-root>]
      │
      ├─ --path 지정됨 → 프로젝트 선택 화면
      └─ --path 없음  → OS 네이티브 폴더 선택 다이얼로그
                                  │
                            Dashboard (기본)
                        사이드바 메뉴로 화면 전환:
                Dashboard | Task Operations | Resources | Settings
```

### Dashboard — Gantt Chart

frappe-gantt로 Epic/Task를 타임라인으로 표시.
행: Epic(그룹) > Task. 컬럼: 날짜. 색상: 상태별 구분.

### Task Operations — ReactFlow Diagram

**상단 계층 바**: `E001 > [T002] 회원가입 API ▼`
- 클릭 시 팝업: 부모(Epic/Task) + 현재 Task + 직계 자식 표시
- 팝업에서 다른 Task 클릭 → 해당 Task로 이동, 팝업 닫힘

**Operation Flow (ReactFlow)**:
- 선택된 Task의 operation 이력을 위→아래 노드-엣지로 표시
- 각 노드: operation_type, 시간, summary

### IPC Architecture

```
main process                    renderer process
────────────────                ────────────────
better-sqlite3 쿼리  ──IPC──▶  React 상태 업데이트
chokidar watcher     ──IPC──▶  자동 리렌더
dialog.showOpenDialog ◀─IPC──  폴더 선택 요청
```

renderer에서 직접 DB 접근 금지 (보안).

---

## 8. Testing Strategy

| 레이어 | 테스트 종류 | 도구 |
|--------|------------|------|
| core | 단위 테스트 — 쿼리 함수, watcher | Vitest + 임시 SQLite DB |
| tui | 컴포넌트 테스트 — 렌더링, 키보드 네비게이션 | Vitest + ink-testing-library |
| electron | 컴포넌트 테스트 — React 컴포넌트 단위 | Vitest + React Testing Library |
| electron | E2E — 앱 실행, 화면 전환, 데이터 표시 | Playwright |

- **테스트 픽스처**: `fixtures/fixture.db` — 2개 Epic, 5개 Task, 10개 Operation 샘플 데이터
- **TDD 적용**: core 쿼리 함수 전체, 핵심 컴포넌트 렌더링 로직
- **E2E**: 구현 완료 후 작성
