# TaskBoard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** TaskOps 프로젝트의 작업 현황을 시각화하는 TUI(Ink)와 Electron 두 앱을 pnpm 모노레포로 구현한다.

**Architecture:** pnpm workspaces 모노레포. `@taskboard/core`가 SQLite 읽기/감시 로직을 담당하고, `@taskboard/tui`(Ink 5)와 `@taskboard/electron`(Electron 33 + React 18 + Vite)이 각각 UI를 구현한다. 모든 DB 접근은 읽기 전용이며 Electron은 main 프로세스에서만 DB에 접근한다.

**Tech Stack:** TypeScript, pnpm workspaces, better-sqlite3, chokidar, Ink 5, Electron 33, React 18, Vite, Tailwind CSS, frappe-gantt, ReactFlow, Vitest, ink-testing-library, React Testing Library, Playwright

**Design Doc:** `docs/plans/2026-03-15-taskboard-design.md`

---

## 진행 현황

- [x] Task 1: 모노레포 스캐폴딩
- [x] Task 2: Core — 타입 모델 정의
- [x] Task 3: Core — DB 연결
- [x] Task 4: Core — 쿼리 함수
- [x] Task 5: Core — DB 파일 감시 (Watcher)
- [x] Task 6: 테스트 픽스처 DB 생성
- [x] Task 7: TUI — 진입점 & 앱 쉘
- [x] Task 8: TUI — ProjectSelect 화면
- [x] Task 9: TUI — Dashboard 화면
- [x] Task 10: TUI — TaskOperations 화면
- [x] Task 11: TUI — Resources 화면
- [x] Task 12: TUI — Settings 화면
- [x] Task 13: Electron — Main 프로세스 (IPC + Watcher)
- [x] Task 14: Electron — 앱 쉘 & 사이드바
- [x] Task 15: Electron — ProjectSelect 화면
- [x] Task 16: Electron — Dashboard 화면 (Gantt)
- [x] Task 17: Electron — TaskOperations 화면 (ReactFlow)
- [x] Task 18: Electron — Resources 화면
- [x] Task 19: Electron — Settings 화면
- [x] Task 20: Electron — E2E 테스트 (Playwright)
- [x] Task 21: 패키징 & npx 실행 설정

---

## Task 1: 모노레포 스캐폴딩

**Files:**
- Create: `taskboard/package.json`
- Create: `taskboard/pnpm-workspace.yaml`
- Create: `taskboard/packages/core/package.json`
- Create: `taskboard/packages/core/tsconfig.json`
- Create: `taskboard/packages/core/src/index.ts`
- Create: `taskboard/packages/tui/package.json`
- Create: `taskboard/packages/tui/tsconfig.json`
- Create: `taskboard/packages/electron/package.json`
- Create: `taskboard/packages/electron/tsconfig.json`

**Step 1: taskboard/ 디렉토리 구조 생성**

```bash
mkdir -p taskboard/packages/core/src
mkdir -p taskboard/packages/tui/src/screens
mkdir -p taskboard/packages/tui/tests
mkdir -p taskboard/packages/electron/src/main
mkdir -p taskboard/packages/electron/src/renderer/screens
mkdir -p taskboard/packages/electron/tests
mkdir -p taskboard/fixtures
```

**Step 2: 루트 package.json 작성**

```json
// taskboard/package.json
{
  "name": "taskboard",
  "private": true,
  "scripts": {
    "build": "pnpm -r build",
    "test": "pnpm -r test",
    "dev:tui": "pnpm --filter @taskboard/tui dev",
    "dev:electron": "pnpm --filter @taskboard/electron dev"
  },
  "devDependencies": {
    "typescript": "^5.4.0"
  }
}
```

**Step 3: pnpm-workspace.yaml 작성**

```yaml
# taskboard/pnpm-workspace.yaml
packages:
  - 'packages/*'
```

**Step 4: core/package.json 작성**

```json
// taskboard/packages/core/package.json
{
  "name": "@taskboard/core",
  "version": "0.1.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "better-sqlite3": "^9.4.3",
    "chokidar": "^3.6.0"
  },
  "devDependencies": {
    "@types/better-sqlite3": "^7.6.9",
    "@types/node": "^20.0.0",
    "vitest": "^1.4.0"
  }
}
```

**Step 5: core/tsconfig.json 작성**

```json
// taskboard/packages/core/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "CommonJS",
    "lib": ["ES2020"],
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "declaration": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"],
  "exclude": ["dist", "node_modules"]
}
```

**Step 6: core/src/index.ts 작성 (re-export 진입점)**

```typescript
// taskboard/packages/core/src/index.ts
export * from './models'
export * from './db'
export * from './queries'
export * from './watcher'
```

**Step 7: tui/package.json 작성**

```json
// taskboard/packages/tui/package.json
{
  "name": "@taskboard/tui",
  "version": "0.1.0",
  "bin": {
    "taskboard-tui": "dist/index.js"
  },
  "scripts": {
    "dev": "ts-node src/index.tsx",
    "build": "tsc",
    "test": "vitest run"
  },
  "dependencies": {
    "@taskboard/core": "workspace:*",
    "ink": "^5.0.1",
    "ink-select-input": "^5.0.0",
    "ink-text-input": "^6.0.0",
    "react": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/node": "^20.0.0",
    "ink-testing-library": "^3.0.0",
    "ts-node": "^10.9.2",
    "typescript": "^5.4.0",
    "vitest": "^1.4.0"
  }
}
```

**Step 8: tui/tsconfig.json 작성**

```json
// taskboard/packages/tui/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "CommonJS",
    "jsx": "react",
    "lib": ["ES2020"],
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"],
  "exclude": ["dist", "node_modules"]
}
```

**Step 9: electron/package.json 작성**

```json
// taskboard/packages/electron/package.json
{
  "name": "@taskboard/electron",
  "version": "0.1.0",
  "main": "dist/main/index.js",
  "scripts": {
    "dev": "concurrently \"vite\" \"wait-on http://localhost:5173 && electron .\"",
    "build": "vite build && tsc -p tsconfig.main.json",
    "test": "vitest run",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "@taskboard/core": "workspace:*",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "reactflow": "^11.11.3",
    "frappe-gantt": "^0.6.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@types/node": "^20.0.0",
    "@vitejs/plugin-react": "^4.2.1",
    "@playwright/test": "^1.42.1",
    "autoprefixer": "^10.4.18",
    "concurrently": "^8.2.2",
    "electron": "^33.0.0",
    "electron-builder": "^24.13.3",
    "postcss": "^8.4.35",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.4.0",
    "vite": "^5.1.5",
    "vitest": "^1.4.0",
    "wait-on": "^7.2.0"
  }
}
```

**Step 10: electron/tsconfig.json (renderer용) 작성**

```json
// taskboard/packages/electron/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "jsx": "react-jsx",
    "lib": ["ES2020", "DOM"],
    "outDir": "dist/renderer",
    "rootDir": "src/renderer",
    "strict": true,
    "moduleResolution": "bundler",
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/renderer"],
  "exclude": ["dist", "node_modules"]
}
```

**Step 11: electron/tsconfig.main.json (main process용) 작성**

```json
// taskboard/packages/electron/tsconfig.main.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "CommonJS",
    "lib": ["ES2020"],
    "outDir": "dist/main",
    "rootDir": "src/main",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/main"],
  "exclude": ["dist", "node_modules"]
}
```

**Step 12: 의존성 설치**

```bash
cd taskboard && pnpm install
```

Expected: 모든 패키지 설치 완료, node_modules 생성

**Step 13: Commit**

```bash
git add taskboard/
git commit -m "feat(taskboard): scaffold pnpm monorepo with core, tui, electron packages"
```

---

## Task 2: Core — 타입 모델 정의

**Files:**
- Create: `taskboard/packages/core/src/models.ts`

**Step 1: models.ts 작성**

```typescript
// taskboard/packages/core/src/models.ts

export type TaskStatus = 'todo' | 'in_progress' | 'interrupted' | 'done' | 'cancelled'
export type TaskType = 'project' | 'epic' | 'task' | 'objective'
export type OperationType = 'start' | 'progress' | 'complete' | 'error' | 'interrupt'
export type ResourceType = 'input' | 'output' | 'reference' | 'intermediate'

export interface Task {
  id: string
  project_id: string
  type: TaskType
  title: string
  description?: string
  status: TaskStatus
  parent_id?: string
  todo?: string
  interrupt?: string
  milestone_target?: string
  due_date?: string
  seq_order?: number
  parallel_group?: string
  depends_on?: string[]   // DB에서 JSON 파싱 후
  created_at: string
  updated_at: string
}

export interface Operation {
  id: number
  task_id: string
  operation_type: OperationType
  agent_platform?: string
  summary?: string
  details?: string
  subagent_used?: number
  subagent_result?: string
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface Resource {
  id: number
  task_id: string
  file_path: string
  description?: string
  res_type: ResourceType
  created_at: string
}

export interface Setting {
  key: string
  value: string
  description?: string
  updated_at: string
}

export interface ProjectInfo {
  id: string
  title: string
  status: TaskStatus
  created_at: string
}

export interface EpicWithTasks {
  epic: Task
  tasks: TaskWithChildren[]
}

export interface TaskWithChildren {
  task: Task
  children: Task[]   // SubTask 목록
}

export interface ProjectSummary {
  project: ProjectInfo
  totalEpics: number
  totalTasks: number
  tasksByStatus: Record<TaskStatus, number>
}
```

**Step 2: index.ts에 이미 export 포함되어 있으므로 빌드 확인**

```bash
cd taskboard && pnpm --filter @taskboard/core build
```

Expected: `packages/core/dist/` 생성, 오류 없음

**Step 3: Commit**

```bash
git add taskboard/packages/core/src/models.ts
git commit -m "feat(core): add TypeScript data models for TaskOps DB schema"
```

---

## Task 3: Core — DB 연결

**Files:**
- Create: `taskboard/packages/core/src/db.ts`
- Create: `taskboard/packages/core/tests/db.test.ts`

**Step 1: 테스트 먼저 작성**

```typescript
// taskboard/packages/core/tests/db.test.ts
import { describe, it, expect, afterEach } from 'vitest'
import { openDb, closeDb } from '../src/db'
import Database from 'better-sqlite3'
import fs from 'fs'
import os from 'os'
import path from 'path'

const tmpDb = () => path.join(os.tmpdir(), `test-${Date.now()}.db`)

describe('openDb', () => {
  const paths: string[] = []

  afterEach(() => {
    paths.forEach(p => { try { fs.unlinkSync(p) } catch {} })
    paths.length = 0
  })

  it('존재하는 DB 파일을 열 수 있다', () => {
    // fixtures/fixture.db는 Task 6에서 생성. 지금은 임시 DB 사용
    const p = tmpDb(); paths.push(p)
    // 빈 SQLite 파일 생성
    const db = new Database(p)
    db.close()
    const conn = openDb(p)
    expect(conn).toBeDefined()
    closeDb(conn)
  })

  it('존재하지 않는 파일이면 에러를 던진다', () => {
    expect(() => openDb('/non/existent/path.db')).toThrow()
  })
})
```

**Step 2: 테스트 실행 — 실패 확인**

```bash
cd taskboard && pnpm --filter @taskboard/core test
```

Expected: FAIL — `openDb` not found

**Step 3: db.ts 구현**

```typescript
// taskboard/packages/core/src/db.ts
import Database from 'better-sqlite3'

export type Db = Database.Database

/**
 * 기존 TaskOps DB 파일을 읽기 전용으로 연다.
 * 파일이 없으면 에러를 던진다.
 */
export function openDb(dbPath: string): Db {
  // readonly 옵션: DB를 수정하지 못하도록 강제
  return new Database(dbPath, { readonly: true })
}

export function closeDb(db: Db): void {
  db.close()
}
```

**Step 4: 테스트 실행 — 통과 확인**

```bash
cd taskboard && pnpm --filter @taskboard/core test
```

Expected: PASS

**Step 5: Commit**

```bash
git add taskboard/packages/core/src/db.ts taskboard/packages/core/tests/db.test.ts
git commit -m "feat(core): add read-only SQLite DB connection"
```

---

## Task 4: Core — 쿼리 함수

**Files:**
- Create: `taskboard/packages/core/src/queries.ts`
- Create: `taskboard/packages/core/tests/queries.test.ts`

> **Note:** 이 태스크는 Task 6(픽스처 DB)가 완료된 후 실행한다. Task 6을 먼저 완료하거나, 인메모리 DB로 테스트할 수 있다.

**Step 1: 테스트용 인메모리 DB 헬퍼 작성**

```typescript
// taskboard/packages/core/tests/helpers.ts
import Database from 'better-sqlite3'

export function createTestDb() {
  const db = new Database(':memory:')
  db.exec(`
    CREATE TABLE tasks (
      id TEXT PRIMARY KEY, project_id TEXT NOT NULL, type TEXT NOT NULL,
      title TEXT NOT NULL, description TEXT, status TEXT NOT NULL DEFAULT 'todo',
      parent_id TEXT, todo TEXT, interrupt TEXT, milestone_target TEXT, due_date TEXT,
      seq_order INTEGER, parallel_group TEXT, depends_on TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE operations (
      id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
      operation_type TEXT NOT NULL, agent_platform TEXT, summary TEXT,
      details TEXT, subagent_used INTEGER DEFAULT 0, subagent_result TEXT,
      started_at TEXT, completed_at TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE resources (
      id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
      file_path TEXT NOT NULL, description TEXT,
      res_type TEXT NOT NULL DEFAULT 'reference',
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE settings (
      key TEXT PRIMARY KEY, value TEXT NOT NULL, description TEXT,
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
  `)

  // 샘플 데이터 삽입
  db.exec(`
    INSERT INTO tasks VALUES ('TST','TST','project','Test Project',NULL,'in_progress',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,datetime('now'),datetime('now'));
    INSERT INTO tasks VALUES ('TST-E001','TST','epic','인증 시스템',NULL,'in_progress','TST',NULL,NULL,NULL,NULL,NULL,NULL,NULL,datetime('now'),datetime('now'));
    INSERT INTO tasks VALUES ('TST-T001','TST','task','로그인 API',NULL,'done','TST-E001',NULL,NULL,NULL,NULL,1,NULL,NULL,datetime('now'),datetime('now'));
    INSERT INTO tasks VALUES ('TST-T002','TST','task','회원가입 API',NULL,'in_progress','TST-E001',NULL,NULL,NULL,NULL,2,NULL,NULL,datetime('now'),datetime('now'));
    INSERT INTO tasks VALUES ('TST-T003','TST','task','JWT 검증',NULL,'todo','TST-E001',NULL,NULL,NULL,NULL,3,NULL,'["TST-T001"]',datetime('now'),datetime('now'));
    INSERT INTO operations VALUES (1,'TST-T001','start','claude_code',NULL,NULL,0,NULL,datetime('now'),NULL,datetime('now'));
    INSERT INTO operations VALUES (2,'TST-T001','complete','claude_code','로그인 API 완료',NULL,0,NULL,datetime('now'),datetime('now'),datetime('now'));
    INSERT INTO resources VALUES (1,'TST-T001','./docs/spec.md','API 스펙','input',datetime('now'));
    INSERT INTO settings VALUES ('autonomy_level','moderate','Agent 자율성',datetime('now'));
  `)

  return db
}
```

**Step 2: 쿼리 테스트 작성**

```typescript
// taskboard/packages/core/tests/queries.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { createTestDb } from './helpers'
import {
  getProject, getEpicsWithTasks, getWorkflowOrder,
  getOperations, getResources, getSettings, getProjectList
} from '../src/queries'
import type { Db } from '../src/db'

let db: Db

beforeEach(() => { db = createTestDb() })

describe('getProject', () => {
  it('프로젝트 기본 정보를 반환한다', () => {
    const p = getProject(db)
    expect(p?.id).toBe('TST')
    expect(p?.title).toBe('Test Project')
  })
})

describe('getEpicsWithTasks', () => {
  it('Epic과 하위 Task를 계층으로 반환한다', () => {
    const epics = getEpicsWithTasks(db)
    expect(epics).toHaveLength(1)
    expect(epics[0].epic.id).toBe('TST-E001')
    expect(epics[0].tasks).toHaveLength(3)
  })
})

describe('getWorkflowOrder', () => {
  it('seq_order 순으로 정렬된 Task를 반환한다', () => {
    const tasks = getWorkflowOrder(db)
    expect(tasks[0].id).toBe('TST-T001')
    expect(tasks[1].id).toBe('TST-T002')
    expect(tasks[2].id).toBe('TST-T003')
  })
})

describe('getOperations', () => {
  it('전체 operations를 반환한다', () => {
    const ops = getOperations(db)
    expect(ops).toHaveLength(2)
  })

  it('특정 task의 operations만 반환한다', () => {
    const ops = getOperations(db, 'TST-T001')
    expect(ops).toHaveLength(2)
    expect(ops.every(o => o.task_id === 'TST-T001')).toBe(true)
  })
})

describe('getResources', () => {
  it('전체 resources를 반환한다', () => {
    const res = getResources(db)
    expect(res).toHaveLength(1)
  })
})

describe('getSettings', () => {
  it('설정 목록을 반환한다', () => {
    const settings = getSettings(db)
    expect(settings.length).toBeGreaterThan(0)
    expect(settings[0].key).toBe('autonomy_level')
  })
})
```

**Step 3: 테스트 실행 — 실패 확인**

```bash
cd taskboard && pnpm --filter @taskboard/core test
```

Expected: FAIL — `getProject` not found

**Step 4: queries.ts 구현**

```typescript
// taskboard/packages/core/src/queries.ts
import type { Db } from './db'
import type {
  Task, Operation, Resource, Setting,
  ProjectInfo, EpicWithTasks, TaskWithChildren
} from './models'
import fs from 'fs'
import path from 'path'

function parseTask(row: any): Task {
  return {
    ...row,
    depends_on: row.depends_on ? JSON.parse(row.depends_on) : undefined,
  }
}

export function getProject(db: Db): ProjectInfo | undefined {
  const row = db.prepare(
    "SELECT id, title, status, created_at FROM tasks WHERE type = 'project' LIMIT 1"
  ).get() as any
  return row ?? undefined
}

export function getEpicsWithTasks(db: Db): EpicWithTasks[] {
  const epics = db.prepare(
    "SELECT * FROM tasks WHERE type = 'epic' ORDER BY seq_order ASC, created_at ASC"
  ).all() as any[]

  return epics.map(epicRow => {
    const epic = parseTask(epicRow)
    const taskRows = db.prepare(
      "SELECT * FROM tasks WHERE type = 'task' AND parent_id = ? ORDER BY seq_order ASC, created_at ASC"
    ).all(epic.id) as any[]

    const tasks: TaskWithChildren[] = taskRows.map(taskRow => {
      const task = parseTask(taskRow)
      const childRows = db.prepare(
        "SELECT * FROM tasks WHERE type = 'task' AND parent_id = ? ORDER BY seq_order ASC, created_at ASC"
      ).all(task.id) as any[]
      return { task, children: childRows.map(parseTask) }
    })

    return { epic, tasks }
  })
}

export function getWorkflowOrder(db: Db): Task[] {
  const rows = db.prepare(
    "SELECT * FROM tasks WHERE type = 'task' ORDER BY seq_order ASC NULLS LAST, created_at ASC"
  ).all() as any[]
  return rows.map(parseTask)
}

export function getOperations(db: Db, taskId?: string): Operation[] {
  if (taskId) {
    return db.prepare(
      "SELECT * FROM operations WHERE task_id = ? ORDER BY created_at ASC"
    ).all(taskId) as Operation[]
  }
  return db.prepare(
    "SELECT * FROM operations ORDER BY created_at ASC"
  ).all() as Operation[]
}

export function getResources(db: Db, taskId?: string): Resource[] {
  if (taskId) {
    return db.prepare(
      "SELECT * FROM resources WHERE task_id = ? ORDER BY created_at ASC"
    ).all(taskId) as Resource[]
  }
  return db.prepare(
    "SELECT * FROM resources ORDER BY created_at ASC"
  ).all() as Resource[]
}

export function getSettings(db: Db): Setting[] {
  return db.prepare("SELECT * FROM settings ORDER BY key ASC").all() as Setting[]
}

/**
 * TaskOps 루트 폴더 내의 프로젝트 목록을 스캔한다.
 * 각 하위 폴더에서 taskops.db 파일이 있는 것만 반환.
 */
export function getProjectList(taskopsRoot: string): Array<{ name: string; dbPath: string }> {
  if (!fs.existsSync(taskopsRoot)) return []
  return fs.readdirSync(taskopsRoot)
    .filter(name => {
      const dbPath = path.join(taskopsRoot, name, 'taskops.db')
      return fs.existsSync(dbPath)
    })
    .map(name => ({
      name,
      dbPath: path.join(taskopsRoot, name, 'taskops.db'),
    }))
}

export function getProjectSummary(db: Db) {
  const project = getProject(db)
  const taskRows = db.prepare(
    "SELECT status, COUNT(*) as count FROM tasks WHERE type IN ('task') GROUP BY status"
  ).all() as Array<{ status: string; count: number }>

  const epicCount = (db.prepare(
    "SELECT COUNT(*) as count FROM tasks WHERE type = 'epic'"
  ).get() as any).count

  const tasksByStatus: Record<string, number> = {}
  taskRows.forEach(r => { tasksByStatus[r.status] = r.count })
  const totalTasks = taskRows.reduce((sum, r) => sum + r.count, 0)

  return { project, totalEpics: epicCount, totalTasks, tasksByStatus }
}
```

**Step 5: 테스트 실행 — 통과 확인**

```bash
cd taskboard && pnpm --filter @taskboard/core test
```

Expected: All PASS

**Step 6: Commit**

```bash
git add taskboard/packages/core/src/queries.ts taskboard/packages/core/tests/
git commit -m "feat(core): add query functions for all TaskOps DB tables"
```

---

## Task 5: Core — DB 파일 감시 (Watcher)

**Files:**
- Create: `taskboard/packages/core/src/watcher.ts`
- Create: `taskboard/packages/core/tests/watcher.test.ts`

**Step 1: 테스트 작성**

```typescript
// taskboard/packages/core/tests/watcher.test.ts
import { describe, it, expect, vi } from 'vitest'
import { watch } from '../src/watcher'
import fs from 'fs'
import os from 'os'
import path from 'path'

describe('watch', () => {
  it('unwatch 함수를 반환한다', () => {
    const tmpPath = path.join(os.tmpdir(), `watch-test-${Date.now()}.db`)
    fs.writeFileSync(tmpPath, '')
    const unwatch = watch(tmpPath, vi.fn())
    expect(typeof unwatch).toBe('function')
    unwatch()
    fs.unlinkSync(tmpPath)
  })

  it('파일 변경 시 콜백이 호출된다', async () => {
    const tmpPath = path.join(os.tmpdir(), `watch-test-${Date.now()}.db`)
    fs.writeFileSync(tmpPath, 'initial')

    const callback = vi.fn()
    const unwatch = watch(tmpPath, callback)

    await new Promise(r => setTimeout(r, 200))
    fs.writeFileSync(tmpPath, 'changed')
    await new Promise(r => setTimeout(r, 500))

    expect(callback).toHaveBeenCalled()
    unwatch()
    fs.unlinkSync(tmpPath)
  })
})
```

**Step 2: 테스트 실행 — 실패 확인**

```bash
cd taskboard && pnpm --filter @taskboard/core test
```

Expected: FAIL — `watch` not found

**Step 3: watcher.ts 구현**

```typescript
// taskboard/packages/core/src/watcher.ts
import chokidar from 'chokidar'

type UnwatchFn = () => void

/**
 * DB 파일 변경을 감시한다.
 * chokidar(fs.watch 기반) 우선, 실패 시 3초 폴링으로 fallback.
 * @returns unwatch 함수
 */
export function watch(dbPath: string, onChange: () => void): UnwatchFn {
  let watcher: ReturnType<typeof chokidar.watch> | null = null
  let pollTimer: ReturnType<typeof setInterval> | null = null
  let lastMtime = 0

  try {
    watcher = chokidar.watch(dbPath, {
      persistent: true,
      usePolling: false,
      ignoreInitial: true,
    })
    watcher.on('change', onChange)
    watcher.on('error', () => startPolling())
  } catch {
    startPolling()
  }

  function startPolling() {
    if (pollTimer) return
    pollTimer = setInterval(() => {
      try {
        const { mtimeMs } = require('fs').statSync(dbPath)
        if (lastMtime && mtimeMs !== lastMtime) onChange()
        lastMtime = mtimeMs
      } catch {}
    }, 3000)
  }

  return () => {
    watcher?.close()
    if (pollTimer) clearInterval(pollTimer)
  }
}
```

**Step 4: 테스트 실행 — 통과 확인**

```bash
cd taskboard && pnpm --filter @taskboard/core test
```

Expected: All PASS

**Step 5: core 빌드 확인**

```bash
cd taskboard && pnpm --filter @taskboard/core build
```

Expected: `dist/` 생성, 오류 없음

**Step 6: Commit**

```bash
git add taskboard/packages/core/src/watcher.ts taskboard/packages/core/tests/watcher.test.ts
git commit -m "feat(core): add DB file watcher with chokidar + polling fallback"
```

---

## Task 6: 테스트 픽스처 DB 생성

**Files:**
- Create: `taskboard/fixtures/create-fixture.ts`
- Create: `taskboard/fixtures/fixture.db` (스크립트 실행으로 생성)

**Step 1: 픽스처 생성 스크립트 작성**

```typescript
// taskboard/fixtures/create-fixture.ts
/**
 * 테스트용 샘플 DB 생성 스크립트.
 * 실행: npx ts-node create-fixture.ts
 * 결과: fixture.db 생성
 */
import Database from 'better-sqlite3'
import path from 'path'

const db = new Database(path.join(__dirname, 'fixture.db'))

db.exec(`
  CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, type TEXT NOT NULL,
    title TEXT NOT NULL, description TEXT, status TEXT NOT NULL DEFAULT 'todo',
    parent_id TEXT, todo TEXT, interrupt TEXT, milestone_target TEXT, due_date TEXT,
    seq_order INTEGER, parallel_group TEXT, depends_on TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
    operation_type TEXT NOT NULL, agent_platform TEXT, summary TEXT,
    details TEXT, subagent_used INTEGER DEFAULT 0, subagent_result TEXT,
    started_at TEXT, completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
    file_path TEXT NOT NULL, description TEXT,
    res_type TEXT NOT NULL DEFAULT 'reference',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY, value TEXT NOT NULL, description TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
`)

// Project
db.prepare("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))")
  .run('FIX','FIX','project','Fixture Project',null,'in_progress',null,null,null,null,null,null,null,null)

// Epics
db.prepare("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))")
  .run('FIX-E001','FIX','epic','인증 시스템 구현','로그인/회원가입 API','in_progress','FIX',null,null,null,null,1,null,null)
db.prepare("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))")
  .run('FIX-E002','FIX','epic','대시보드 구현','통계 화면','todo','FIX',null,null,null,null,2,null,null)

// Tasks under E001
db.prepare("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))")
  .run('FIX-T001','FIX','task','로그인 API 구현',null,'done','FIX-E001',null,null,null,null,1,null,null)
db.prepare("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))")
  .run('FIX-T002','FIX','task','회원가입 API 구현',null,'in_progress','FIX-E001',null,null,null,null,2,null,null)
db.prepare("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))")
  .run('FIX-T003','FIX','task','JWT 검증 구현',null,'todo','FIX-E001',null,null,null,null,3,null,'["FIX-T001"]')

// SubTasks under T002
db.prepare("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))")
  .run('FIX-T004','FIX','task','입력값 검증',null,'in_progress','FIX-T002',null,null,null,null,1,null,null)
db.prepare("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))")
  .run('FIX-T005','FIX','task','DB 저장',null,'todo','FIX-T002',null,null,null,null,2,null,null)

// Operations for T001
db.prepare("INSERT INTO operations (task_id,operation_type,agent_platform,summary,started_at,completed_at) VALUES (?,?,?,?,?,?)")
  .run('FIX-T001','start','claude_code',null,'2026-03-15 10:00:00',null)
db.prepare("INSERT INTO operations (task_id,operation_type,agent_platform,summary) VALUES (?,?,?,?)")
  .run('FIX-T001','progress','claude_code','DB 스키마 작성 완료')
db.prepare("INSERT INTO operations (task_id,operation_type,agent_platform,summary) VALUES (?,?,?,?)")
  .run('FIX-T001','progress','claude_code','엔드포인트 2/3 완료')
db.prepare("INSERT INTO operations (task_id,operation_type,agent_platform,summary,completed_at) VALUES (?,?,?,?,?)")
  .run('FIX-T001','complete','claude_code','로그인 API 구현 완료','2026-03-15 11:00:00')

// Operations for T002
db.prepare("INSERT INTO operations (task_id,operation_type,agent_platform,summary,started_at) VALUES (?,?,?,?,?)")
  .run('FIX-T002','start','claude_code',null,'2026-03-15 11:05:00')
db.prepare("INSERT INTO operations (task_id,operation_type,agent_platform,summary) VALUES (?,?,?,?)")
  .run('FIX-T002','progress','claude_code','입력값 검증 로직 작성 중')

// Resources
db.prepare("INSERT INTO resources (task_id,file_path,description,res_type) VALUES (?,?,?,?)")
  .run('FIX-T001','./docs/api-spec.md','API 스펙 문서','input')
db.prepare("INSERT INTO resources (task_id,file_path,description,res_type) VALUES (?,?,?,?)")
  .run('FIX-T001','./src/auth/login.py','로그인 구현 파일','output')
db.prepare("INSERT INTO resources (task_id,file_path,description,res_type) VALUES (?,?,?,?)")
  .run('FIX-T002','./resources/FIX-T002_draft.md','중간 결과물','intermediate')

// Settings
db.prepare("INSERT INTO settings (key,value,description) VALUES (?,?,?)")
  .run('autonomy_level','moderate','Agent 자율성 수준')
db.prepare("INSERT INTO settings (key,value,description) VALUES (?,?,?)")
  .run('commit_style','conventional','커밋 메시지 스타일')
db.prepare("INSERT INTO settings (key,value,description) VALUES (?,?,?)")
  .run('use_subagent','true','Sub Agent 사용 허용')

db.close()
console.log('fixture.db created successfully')
```

**Step 2: 스크립트 실행**

```bash
cd taskboard/fixtures && npx ts-node --project ../packages/core/tsconfig.json create-fixture.ts
```

Expected: `fixture.db` 생성

**Step 3: Commit**

```bash
git add taskboard/fixtures/
git commit -m "feat(taskboard): add test fixture DB with sample project data"
```

---

## Task 7: TUI — 진입점 & 앱 쉘

**Files:**
- Create: `taskboard/packages/tui/src/index.tsx`
- Create: `taskboard/packages/tui/src/App.tsx`
- Create: `taskboard/packages/tui/src/useTaskBoard.ts`

**Step 1: 앱 상태 훅 작성 (useTaskBoard.ts)**

```typescript
// taskboard/packages/tui/src/useTaskBoard.ts
import { useState, useEffect, useCallback } from 'react'
import { openDb, closeDb, getProject, getEpicsWithTasks,
         getWorkflowOrder, getOperations, getResources,
         getSettings, watch } from '@taskboard/core'
import type { Db, EpicWithTasks, Operation, Resource, Setting, ProjectInfo } from '@taskboard/core'

export type Screen = 'dashboard' | 'taskops' | 'resources' | 'settings'

interface TaskBoardState {
  project: ProjectInfo | undefined
  epics: EpicWithTasks[]
  operations: Operation[]
  resources: Resource[]
  settings: Setting[]
  selectedTaskId: string | null
  screen: Screen
  error: string | null
}

export function useTaskBoard(dbPath: string) {
  const [state, setState] = useState<TaskBoardState>({
    project: undefined, epics: [], operations: [], resources: [],
    settings: [], selectedTaskId: null, screen: 'dashboard', error: null,
  })

  const reload = useCallback(() => {
    let db: Db | null = null
    try {
      db = openDb(dbPath)
      setState(prev => ({
        ...prev,
        project: getProject(db!),
        epics: getEpicsWithTasks(db!),
        operations: getOperations(db!),
        resources: getResources(db!),
        settings: getSettings(db!),
        error: null,
      }))
    } catch (e) {
      setState(prev => ({ ...prev, error: String(e) }))
    } finally {
      if (db) closeDb(db)
    }
  }, [dbPath])

  useEffect(() => {
    reload()
    const unwatch = watch(dbPath, reload)
    return () => unwatch()
  }, [dbPath, reload])

  const setScreen = (screen: Screen) => setState(prev => ({ ...prev, screen }))
  const setSelectedTask = (id: string | null) => setState(prev => ({ ...prev, selectedTaskId: id }))

  return { ...state, reload, setScreen, setSelectedTask }
}
```

**Step 2: App.tsx 작성 (화면 라우팅)**

```tsx
// taskboard/packages/tui/src/App.tsx
import React from 'react'
import { Box, Text, useInput } from 'ink'
import { useTaskBoard, Screen } from './useTaskBoard'
import { Dashboard } from './screens/Dashboard'
import { TaskOperations } from './screens/TaskOperations'
import { Resources } from './screens/Resources'
import { Settings } from './screens/Settings'

const SCREENS: Screen[] = ['dashboard', 'taskops', 'resources', 'settings']
const SCREEN_LABELS: Record<Screen, string> = {
  dashboard: 'Dashboard',
  taskops: 'Task Ops',
  resources: 'Resources',
  settings: 'Settings',
}

interface Props {
  dbPath: string
}

export function App({ dbPath }: Props) {
  const board = useTaskBoard(dbPath)

  useInput((input, key) => {
    if (input === 'q' || input === 'Q') process.exit(0)
    if (input === 'r' || input === 'R') board.reload()
    if (key.tab) {
      const idx = SCREENS.indexOf(board.screen)
      board.setScreen(SCREENS[(idx + 1) % SCREENS.length])
    }
  })

  if (board.error) {
    return <Text color="red">Error: {board.error}</Text>
  }

  return (
    <Box flexDirection="column" height="100%">
      {/* 탭 네비게이션 */}
      <Box borderStyle="single" paddingX={1}>
        {SCREENS.map((s, i) => (
          <Box key={s} marginRight={2}>
            <Text
              color={board.screen === s ? 'cyan' : 'white'}
              bold={board.screen === s}
            >
              {board.screen === s ? `[${SCREEN_LABELS[s]}]` : SCREEN_LABELS[s]}
            </Text>
          </Box>
        ))}
        <Box marginLeft={2}>
          <Text dimColor>[Tab]전환 [R]새로고침 [Q]종료</Text>
        </Box>
      </Box>

      {/* 화면 컨텐츠 */}
      <Box flexGrow={1}>
        {board.screen === 'dashboard' && <Dashboard {...board} />}
        {board.screen === 'taskops' && <TaskOperations {...board} />}
        {board.screen === 'resources' && <Resources resources={board.resources} />}
        {board.screen === 'settings' && <Settings settings={board.settings} />}
      </Box>
    </Box>
  )
}
```

**Step 3: index.tsx (진입점) 작성**

```tsx
// taskboard/packages/tui/src/index.tsx
#!/usr/bin/env node
import React from 'react'
import { render } from 'ink'
import { App } from './App'
import { ProjectSelect } from './screens/ProjectSelect'
import path from 'path'

const args = process.argv.slice(2)
const pathIdx = args.indexOf('--path')
const taskopsRoot = pathIdx !== -1 ? path.resolve(args[pathIdx + 1]) : null

if (taskopsRoot) {
  // 프로젝트 선택 화면으로
  render(<ProjectSelect taskopsRoot={taskopsRoot} />)
} else {
  // 폴더 입력 화면으로
  render(<ProjectSelect taskopsRoot={null} />)
}
```

**Step 4: Commit**

```bash
git add taskboard/packages/tui/src/
git commit -m "feat(tui): add app shell, screen routing, and state hook"
```

---

## Task 8: TUI — ProjectSelect 화면

**Files:**
- Create: `taskboard/packages/tui/src/screens/ProjectSelect.tsx`
- Create: `taskboard/packages/tui/tests/ProjectSelect.test.tsx`

**Step 1: 테스트 작성**

```tsx
// taskboard/packages/tui/tests/ProjectSelect.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render } from 'ink-testing-library'
import React from 'react'

// 실제 파일시스템 접근을 모킹
vi.mock('@taskboard/core', () => ({
  getProjectList: () => [
    { name: 'my-project', dbPath: '/tmp/my-project/taskops.db' }
  ]
}))

import { ProjectSelect } from '../src/screens/ProjectSelect'

describe('ProjectSelect', () => {
  it('프로젝트 목록을 표시한다', () => {
    const { lastFrame } = render(
      <ProjectSelect taskopsRoot="/tmp/taskops" />
    )
    expect(lastFrame()).toContain('my-project')
  })

  it('taskopsRoot가 없으면 경로 입력 UI를 표시한다', () => {
    const { lastFrame } = render(
      <ProjectSelect taskopsRoot={null} />
    )
    expect(lastFrame()).toContain('path')
  })
})
```

**Step 2: 테스트 실행 — 실패 확인**

```bash
cd taskboard && pnpm --filter @taskboard/tui test
```

Expected: FAIL

**Step 3: ProjectSelect.tsx 구현**

```tsx
// taskboard/packages/tui/src/screens/ProjectSelect.tsx
import React, { useState } from 'react'
import { Box, Text, render } from 'ink'
import TextInput from 'ink-text-input'
import SelectInput from 'ink-select-input'
import { getProjectList } from '@taskboard/core'
import { App } from '../App'
import path from 'path'

interface Props {
  taskopsRoot: string | null
}

export function ProjectSelect({ taskopsRoot }: Props) {
  const [rootPath, setRootPath] = useState(taskopsRoot ?? '')
  const [submitted, setSubmitted] = useState(!!taskopsRoot)

  if (!submitted) {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold>TaskBoard</Text>
        <Text dimColor>Enter TaskOps root path:</Text>
        <Box>
          <Text>{'> '}</Text>
          <TextInput
            value={rootPath}
            onChange={setRootPath}
            onSubmit={() => setSubmitted(true)}
          />
        </Box>
      </Box>
    )
  }

  const projects = getProjectList(path.resolve(rootPath))

  if (projects.length === 0) {
    return (
      <Box flexDirection="column" padding={1}>
        <Text color="yellow">No projects found in: {rootPath}</Text>
        <Text dimColor>Make sure the folder contains TaskOps projects (with taskops.db)</Text>
      </Box>
    )
  }

  const items = projects.map(p => ({ label: p.name, value: p.dbPath }))

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Select Project:</Text>
      <SelectInput
        items={items}
        onSelect={item => {
          const { rerender } = render(<App dbPath={item.value} />)
        }}
      />
    </Box>
  )
}
```

**Step 4: 테스트 실행 — 통과 확인**

```bash
cd taskboard && pnpm --filter @taskboard/tui test
```

Expected: PASS

**Step 5: Commit**

```bash
git add taskboard/packages/tui/src/screens/ProjectSelect.tsx taskboard/packages/tui/tests/
git commit -m "feat(tui): add ProjectSelect screen with path input and project list"
```

---

## Task 9: TUI — Dashboard 화면

**Files:**
- Create: `taskboard/packages/tui/src/screens/Dashboard.tsx`
- Create: `taskboard/packages/tui/tests/Dashboard.test.tsx`

**Step 1: 테스트 작성**

```tsx
// taskboard/packages/tui/tests/Dashboard.test.tsx
import { describe, it, expect } from 'vitest'
import { render } from 'ink-testing-library'
import React from 'react'
import { Dashboard } from '../src/screens/Dashboard'

const mockEpics = [{
  epic: { id: 'FIX-E001', title: '인증 시스템', status: 'in_progress', type: 'epic', project_id: 'FIX', created_at: '', updated_at: '' },
  tasks: [
    { task: { id: 'FIX-T001', title: '로그인 API', status: 'done', type: 'task', project_id: 'FIX', parent_id: 'FIX-E001', created_at: '', updated_at: '' }, children: [] },
    { task: { id: 'FIX-T002', title: '회원가입 API', status: 'in_progress', type: 'task', project_id: 'FIX', parent_id: 'FIX-E001', created_at: '', updated_at: '' }, children: [] },
  ]
}]

describe('Dashboard', () => {
  it('Epic 제목을 표시한다', () => {
    const { lastFrame } = render(
      <Dashboard project={undefined} epics={mockEpics} operations={[]} resources={[]} settings={[]} selectedTaskId={null} screen="dashboard" error={null} reload={() => {}} setScreen={() => {}} setSelectedTask={() => {}} />
    )
    expect(lastFrame()).toContain('인증 시스템')
  })

  it('Task 상태 아이콘을 표시한다', () => {
    const { lastFrame } = render(
      <Dashboard project={undefined} epics={mockEpics} operations={[]} resources={[]} settings={[]} selectedTaskId={null} screen="dashboard" error={null} reload={() => {}} setScreen={() => {}} setSelectedTask={() => {}} />
    )
    expect(lastFrame()).toContain('로그인 API')
    expect(lastFrame()).toContain('회원가입 API')
  })
})
```

**Step 2: 테스트 실행 — 실패 확인**

```bash
cd taskboard && pnpm --filter @taskboard/tui test
```

Expected: FAIL

**Step 3: Dashboard.tsx 구현**

```tsx
// taskboard/packages/tui/src/screens/Dashboard.tsx
import React from 'react'
import { Box, Text } from 'ink'
import type { EpicWithTasks, ProjectInfo, TaskStatus } from '@taskboard/core'

const STATUS_ICON: Record<TaskStatus, string> = {
  done: '✓',
  in_progress: '●',
  todo: '○',
  interrupted: '✕',
  cancelled: '—',
}

const STATUS_COLOR: Record<TaskStatus, string> = {
  done: 'green',
  in_progress: 'yellow',
  todo: 'white',
  interrupted: 'red',
  cancelled: 'gray',
}

function ProgressBar({ value, total, width = 20 }: { value: number; total: number; width?: number }) {
  const filled = total > 0 ? Math.round((value / total) * width) : 0
  const bar = '█'.repeat(filled) + '░'.repeat(width - filled)
  const pct = total > 0 ? Math.round((value / total) * 100) : 0
  return <Text>{bar} {pct}%</Text>
}

interface Props {
  project: ProjectInfo | undefined
  epics: EpicWithTasks[]
  [key: string]: any
}

export function Dashboard({ project, epics }: Props) {
  const allTasks = epics.flatMap(e => e.tasks.map(t => t.task))
  const doneTasks = allTasks.filter(t => t.status === 'done').length
  const inProgressTasks = allTasks.filter(t => t.status === 'in_progress').length

  return (
    <Box flexDirection="column" padding={1}>
      {/* 헤더 */}
      <Box borderStyle="single" paddingX={1} marginBottom={1}>
        <Text bold>{project?.title ?? 'Project'}</Text>
        <Text> | </Text>
        <Text>Epics: {epics.length}  Tasks: {allTasks.length}  </Text>
        <Text color="green">Done: {doneTasks}/{allTasks.length}  </Text>
        <Text color="yellow">In Progress: {inProgressTasks}</Text>
      </Box>

      {/* Epic 목록 */}
      {epics.map(({ epic, tasks }) => {
        const epicDone = tasks.filter(t => t.task.status === 'done').length
        return (
          <Box key={epic.id} flexDirection="column" marginBottom={1}>
            <Box>
              <Text bold color="cyan">[{epic.id}] {epic.title}  </Text>
              <ProgressBar value={epicDone} total={tasks.length} />
            </Box>
            {tasks.map(({ task, children }) => (
              <Box key={task.id} flexDirection="column">
                <Box marginLeft={2}>
                  <Text color={STATUS_COLOR[task.status]}>
                    {STATUS_ICON[task.status]} [{task.id}] {task.title}
                  </Text>
                  <Text dimColor>  {task.status}</Text>
                </Box>
                {children.map(child => (
                  <Box key={child.id} marginLeft={4}>
                    <Text color={STATUS_COLOR[child.status]} dimColor>
                      {STATUS_ICON[child.status]} [{child.id}] {child.title}
                    </Text>
                  </Box>
                ))}
              </Box>
            ))}
          </Box>
        )
      })}
    </Box>
  )
}
```

**Step 4: 테스트 실행 — 통과 확인**

```bash
cd taskboard && pnpm --filter @taskboard/tui test
```

Expected: PASS

**Step 5: Commit**

```bash
git add taskboard/packages/tui/src/screens/Dashboard.tsx taskboard/packages/tui/tests/Dashboard.test.tsx
git commit -m "feat(tui): add Dashboard screen with epic/task hierarchy and progress bars"
```

---

## Task 10: TUI — TaskOperations 화면

**Files:**
- Create: `taskboard/packages/tui/src/screens/TaskOperations.tsx`

**Step 1: TaskOperations.tsx 구현**

```tsx
// taskboard/packages/tui/src/screens/TaskOperations.tsx
import React, { useState } from 'react'
import { Box, Text, useInput } from 'ink'
import type { EpicWithTasks, Operation, TaskStatus } from '@taskboard/core'

const OP_ICON: Record<string, string> = {
  start: '▶',
  progress: '│',
  complete: '✓',
  error: '✕',
  interrupt: '⚠',
}

const OP_COLOR: Record<string, string> = {
  start: 'cyan',
  progress: 'white',
  complete: 'green',
  error: 'red',
  interrupt: 'yellow',
}

interface Props {
  epics: EpicWithTasks[]
  operations: Operation[]
  selectedTaskId: string | null
  setSelectedTask: (id: string | null) => void
  [key: string]: any
}

export function TaskOperations({ epics, operations, selectedTaskId, setSelectedTask }: Props) {
  const allTasks = epics.flatMap(e => e.tasks.map(t => t.task))
  const [taskIdx, setTaskIdx] = useState(0)

  const selectedTask = selectedTaskId
    ? allTasks.find(t => t.id === selectedTaskId)
    : allTasks[taskIdx]

  useInput((_, key) => {
    if (key.leftArrow) setTaskIdx(i => Math.max(0, i - 1))
    if (key.rightArrow) setTaskIdx(i => Math.min(allTasks.length - 1, i + 1))
  })

  const taskOps = selectedTask
    ? operations.filter(o => o.task_id === selectedTask.id)
    : []

  return (
    <Box flexDirection="column" padding={1}>
      {/* Task 선택 바 */}
      <Box marginBottom={1} flexWrap="wrap">
        {allTasks.map((t, i) => (
          <Box key={t.id} marginRight={2}>
            <Text
              color={t === selectedTask ? 'cyan' : 'white'}
              bold={t === selectedTask}
            >
              {t === selectedTask ? `▶${t.id}◀` : t.id}
            </Text>
          </Box>
        ))}
      </Box>
      <Text dimColor>[←→] Task 선택</Text>

      {/* Operation Flow */}
      <Box borderStyle="single" flexDirection="column" paddingX={2} marginTop={1}>
        {selectedTask ? (
          <>
            <Text bold>{selectedTask.id}: {selectedTask.title}</Text>
            <Text dimColor>{'─'.repeat(40)}</Text>
            {taskOps.length === 0 && <Text dimColor>No operations recorded</Text>}
            {taskOps.map(op => (
              <Box key={op.id}>
                <Text color={OP_COLOR[op.operation_type]}>
                  {OP_ICON[op.operation_type]} {op.operation_type.padEnd(10)}
                </Text>
                <Text dimColor>{op.created_at.slice(11, 16)}  </Text>
                <Text color={op.agent_platform ? 'blue' : 'white'}>
                  {op.agent_platform ?? ''}{'  '}
                </Text>
                <Text>{op.summary ?? ''}</Text>
              </Box>
            ))}
          </>
        ) : (
          <Text dimColor>No task selected</Text>
        )}
      </Box>
    </Box>
  )
}
```

**Step 2: Commit**

```bash
git add taskboard/packages/tui/src/screens/TaskOperations.tsx
git commit -m "feat(tui): add TaskOperations screen with operation flow display"
```

---

## Task 11: TUI — Resources 화면

**Files:**
- Create: `taskboard/packages/tui/src/screens/Resources.tsx`

**Step 1: Resources.tsx 구현**

```tsx
// taskboard/packages/tui/src/screens/Resources.tsx
import React from 'react'
import { Box, Text } from 'ink'
import type { Resource } from '@taskboard/core'

const TYPE_COLOR: Record<string, string> = {
  input: 'blue',
  output: 'green',
  reference: 'white',
  intermediate: 'yellow',
}

interface Props {
  resources: Resource[]
}

export function Resources({ resources }: Props) {
  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Resources ({resources.length})</Text>
      <Text dimColor>{'─'.repeat(60)}</Text>
      {resources.length === 0 && <Text dimColor>No resources recorded</Text>}
      {resources.map(r => (
        <Box key={r.id} marginBottom={0}>
          <Text color={TYPE_COLOR[r.res_type]}>{r.res_type.padEnd(14)}</Text>
          <Text dimColor>{r.task_id.padEnd(12)}</Text>
          <Text>{r.file_path}</Text>
          {r.description && <Text dimColor>  {r.description}</Text>}
        </Box>
      ))}
    </Box>
  )
}
```

**Step 2: Commit**

```bash
git add taskboard/packages/tui/src/screens/Resources.tsx
git commit -m "feat(tui): add Resources screen"
```

---

## Task 12: TUI — Settings 화면

**Files:**
- Create: `taskboard/packages/tui/src/screens/Settings.tsx`

**Step 1: Settings.tsx 구현**

```tsx
// taskboard/packages/tui/src/screens/Settings.tsx
import React from 'react'
import { Box, Text } from 'ink'
import type { Setting } from '@taskboard/core'

interface Props {
  settings: Setting[]
}

export function Settings({ settings }: Props) {
  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Settings</Text>
      <Text dimColor>{'─'.repeat(50)}</Text>
      {settings.length === 0 && <Text dimColor>No settings found</Text>}
      {settings.map(s => (
        <Box key={s.key} marginBottom={0}>
          <Text color="cyan">{s.key.padEnd(24)}</Text>
          <Text color="yellow">{s.value.padEnd(16)}</Text>
          {s.description && <Text dimColor>{s.description}</Text>}
        </Box>
      ))}
    </Box>
  )
}
```

**Step 2: TUI 전체 빌드 확인**

```bash
cd taskboard && pnpm --filter @taskboard/tui build
```

Expected: `dist/` 생성, 오류 없음

**Step 3: TUI 수동 테스트 (픽스처 DB 사용)**

```bash
cd taskboard && node packages/tui/dist/index.js --path ./fixtures
```

Expected: Dashboard 화면 표시

**Step 4: Commit**

```bash
git add taskboard/packages/tui/src/screens/Settings.tsx
git commit -m "feat(tui): add Settings screen, complete TUI implementation"
```

---

## Task 13: Electron — Main 프로세스 (IPC + Watcher)

**Files:**
- Create: `taskboard/packages/electron/src/main/index.ts`
- Create: `taskboard/packages/electron/src/main/ipc.ts`

**Step 1: IPC 채널 타입 정의 (ipc.ts)**

```typescript
// taskboard/packages/electron/src/main/ipc.ts
// IPC 채널 이름 상수 — main/renderer 양쪽에서 공유
export const IPC = {
  // renderer → main (invoke)
  GET_PROJECT_LIST: 'get-project-list',
  GET_ALL_DATA: 'get-all-data',
  SELECT_FOLDER: 'select-folder',
  // main → renderer (send)
  DB_CHANGED: 'db-changed',
} as const
```

**Step 2: main/index.ts 구현**

```typescript
// taskboard/packages/electron/src/main/index.ts
import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import path from 'path'
import {
  openDb, closeDb, getProject, getEpicsWithTasks, getWorkflowOrder,
  getOperations, getResources, getSettings, getProjectList, watch
} from '@taskboard/core'
import { IPC } from './ipc'

let mainWindow: BrowserWindow | null = null
let currentUnwatch: (() => void) | null = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173')
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  createWindow()

  // 폴더 선택 다이얼로그
  ipcMain.handle(IPC.SELECT_FOLDER, async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory'],
      title: 'Select TaskOps Root Folder',
    })
    return result.canceled ? null : result.filePaths[0]
  })

  // 프로젝트 목록 조회
  ipcMain.handle(IPC.GET_PROJECT_LIST, (_, taskopsRoot: string) => {
    return getProjectList(taskopsRoot)
  })

  // 전체 데이터 조회 (프로젝트 선택 후)
  ipcMain.handle(IPC.GET_ALL_DATA, (_, dbPath: string) => {
    // 이전 watcher 해제
    currentUnwatch?.()

    const db = openDb(dbPath)
    const data = {
      project: getProject(db),
      epics: getEpicsWithTasks(db),
      workflowOrder: getWorkflowOrder(db),
      operations: getOperations(db),
      resources: getResources(db),
      settings: getSettings(db),
    }
    closeDb(db)

    // 새 watcher 등록
    currentUnwatch = watch(dbPath, () => {
      mainWindow?.webContents.send(IPC.DB_CHANGED, dbPath)
    })

    return data
  })
})

app.on('window-all-closed', () => {
  currentUnwatch?.()
  if (process.platform !== 'darwin') app.quit()
})
```

**Step 3: preload.ts 작성**

```typescript
// taskboard/packages/electron/src/main/preload.ts
import { contextBridge, ipcRenderer } from 'electron'
import { IPC } from './ipc'

contextBridge.exposeInMainWorld('taskboard', {
  selectFolder: () => ipcRenderer.invoke(IPC.SELECT_FOLDER),
  getProjectList: (root: string) => ipcRenderer.invoke(IPC.GET_PROJECT_LIST, root),
  getAllData: (dbPath: string) => ipcRenderer.invoke(IPC.GET_ALL_DATA, dbPath),
  onDbChanged: (cb: (dbPath: string) => void) =>
    ipcRenderer.on(IPC.DB_CHANGED, (_, dbPath) => cb(dbPath)),
  offDbChanged: () => ipcRenderer.removeAllListeners(IPC.DB_CHANGED),
})
```

**Step 4: Commit**

```bash
git add taskboard/packages/electron/src/main/
git commit -m "feat(electron): add main process with IPC handlers and DB watcher"
```

---

## Task 14: Electron — 앱 쉘 & 사이드바

**Files:**
- Create: `taskboard/packages/electron/src/renderer/index.html`
- Create: `taskboard/packages/electron/src/renderer/main.tsx`
- Create: `taskboard/packages/electron/src/renderer/App.tsx`
- Create: `taskboard/packages/electron/src/renderer/useTaskBoard.ts`
- Create: `taskboard/packages/electron/src/renderer/components/Sidebar.tsx`
- Create: `taskboard/packages/electron/vite.config.ts`
- Create: `taskboard/packages/electron/tailwind.config.js`

**Step 1: Vite 설정**

```typescript
// taskboard/packages/electron/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  root: 'src/renderer',
  build: {
    outDir: path.resolve(__dirname, 'dist/renderer'),
    emptyOutDir: true,
  },
})
```

**Step 2: Tailwind 설정**

```javascript
// taskboard/packages/electron/tailwind.config.js
export default {
  content: ['./src/renderer/**/*.{tsx,ts,html}'],
  theme: { extend: {} },
  plugins: [],
}
```

**Step 3: index.html**

```html
<!-- taskboard/packages/electron/src/renderer/index.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>TaskBoard</title>
</head>
<body class="bg-gray-950 text-gray-100 h-screen overflow-hidden">
  <div id="root"></div>
  <script type="module" src="/main.tsx"></script>
</body>
</html>
```

**Step 4: useTaskBoard.ts (renderer용 상태 훅)**

```typescript
// taskboard/packages/electron/src/renderer/useTaskBoard.ts
import { useState, useEffect, useCallback } from 'react'
import type { EpicWithTasks, Operation, Resource, Setting, ProjectInfo } from '@taskboard/core'

declare global {
  interface Window {
    taskboard: {
      selectFolder: () => Promise<string | null>
      getProjectList: (root: string) => Promise<Array<{ name: string; dbPath: string }>>
      getAllData: (dbPath: string) => Promise<AllData>
      onDbChanged: (cb: (dbPath: string) => void) => void
      offDbChanged: () => void
    }
  }
}

interface AllData {
  project: ProjectInfo | undefined
  epics: EpicWithTasks[]
  workflowOrder: any[]
  operations: Operation[]
  resources: Resource[]
  settings: Setting[]
}

export type Screen = 'dashboard' | 'taskops' | 'resources' | 'settings'

export function useTaskBoard(dbPath: string | null) {
  const [data, setData] = useState<AllData | null>(null)
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [screen, setScreen] = useState<Screen>('dashboard')

  const reload = useCallback(async (path: string) => {
    const result = await window.taskboard.getAllData(path)
    setData(result)
  }, [])

  useEffect(() => {
    if (!dbPath) return
    reload(dbPath)
    window.taskboard.onDbChanged((changedPath) => {
      if (changedPath === dbPath) reload(dbPath)
    })
    return () => window.taskboard.offDbChanged()
  }, [dbPath, reload])

  return { data, selectedTaskId, setSelectedTaskId, screen, setScreen, reload: () => dbPath && reload(dbPath) }
}
```

**Step 5: Sidebar.tsx**

```tsx
// taskboard/packages/electron/src/renderer/components/Sidebar.tsx
import React from 'react'
import type { Screen } from '../useTaskBoard'

const SCREENS: { id: Screen; label: string; icon: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'taskops', label: 'Task Operations', icon: '🔄' },
  { id: 'resources', label: 'Resources', icon: '📁' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
]

interface Props {
  current: Screen
  onSelect: (s: Screen) => void
  projectName?: string
}

export function Sidebar({ current, onSelect, projectName }: Props) {
  return (
    <div className="w-52 bg-gray-900 border-r border-gray-800 flex flex-col h-full">
      <div className="p-4 border-b border-gray-800">
        <div className="text-xs text-gray-500 uppercase tracking-wider">TaskBoard</div>
        {projectName && (
          <div className="text-sm font-semibold text-white mt-1 truncate">{projectName}</div>
        )}
      </div>
      <nav className="flex-1 p-2">
        {SCREENS.map(s => (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm mb-1 transition-colors
              ${current === s.id
                ? 'bg-blue-600 text-white font-medium'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
          >
            <span>{s.icon}</span>
            <span>{s.label}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}
```

**Step 6: App.tsx**

```tsx
// taskboard/packages/electron/src/renderer/App.tsx
import React, { useState } from 'react'
import { Sidebar } from './components/Sidebar'
import { useTaskBoard } from './useTaskBoard'
import { ProjectSelect } from './screens/ProjectSelect'
import { Dashboard } from './screens/Dashboard'
import { TaskOperations } from './screens/TaskOperations'
import { Resources } from './screens/Resources'
import { Settings } from './screens/Settings'

export function App() {
  const [dbPath, setDbPath] = useState<string | null>(
    // CLI 인자로 전달된 경우 (향후 확장)
    null
  )
  const board = useTaskBoard(dbPath)

  if (!dbPath) {
    return <ProjectSelect onSelect={setDbPath} />
  }

  return (
    <div className="flex h-screen bg-gray-950">
      <Sidebar
        current={board.screen}
        onSelect={board.setScreen}
        projectName={board.data?.project?.title}
      />
      <main className="flex-1 overflow-auto">
        {board.screen === 'dashboard' && <Dashboard data={board.data} />}
        {board.screen === 'taskops' && (
          <TaskOperations
            data={board.data}
            selectedTaskId={board.selectedTaskId}
            setSelectedTask={board.setSelectedTaskId}
          />
        )}
        {board.screen === 'resources' && <Resources resources={board.data?.resources ?? []} />}
        {board.screen === 'settings' && <Settings settings={board.data?.settings ?? []} />}
      </main>
    </div>
  )
}
```

**Step 7: main.tsx**

```tsx
// taskboard/packages/electron/src/renderer/main.tsx
import React from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { App } from './App'

createRoot(document.getElementById('root')!).render(<App />)
```

**Step 8: index.css (Tailwind 임포트)**

```css
/* taskboard/packages/electron/src/renderer/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Step 9: Commit**

```bash
git add taskboard/packages/electron/src/renderer/
git commit -m "feat(electron): add app shell, sidebar, and screen routing"
```

---

## Task 15: Electron — ProjectSelect 화면

**Files:**
- Create: `taskboard/packages/electron/src/renderer/screens/ProjectSelect.tsx`

**Step 1: ProjectSelect.tsx 구현**

```tsx
// taskboard/packages/electron/src/renderer/screens/ProjectSelect.tsx
import React, { useState } from 'react'

interface Props {
  onSelect: (dbPath: string) => void
}

export function ProjectSelect({ onSelect }: Props) {
  const [projects, setProjects] = useState<Array<{ name: string; dbPath: string }>>([])
  const [rootPath, setRootPath] = useState('')

  const handleSelectFolder = async () => {
    const folder = await window.taskboard.selectFolder()
    if (!folder) return
    setRootPath(folder)
    const list = await window.taskboard.getProjectList(folder)
    setProjects(list)
  }

  const handlePathSubmit = async () => {
    if (!rootPath) return
    const list = await window.taskboard.getProjectList(rootPath)
    setProjects(list)
  }

  return (
    <div className="flex items-center justify-center h-screen bg-gray-950">
      <div className="w-96 bg-gray-900 rounded-xl p-8 border border-gray-800">
        <h1 className="text-2xl font-bold text-white mb-2">TaskBoard</h1>
        <p className="text-gray-400 text-sm mb-6">Select a TaskOps project to visualize</p>

        {/* 폴더 선택 */}
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={rootPath}
            onChange={e => setRootPath(e.target.value)}
            placeholder="TaskOps root path..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            onKeyDown={e => e.key === 'Enter' && handlePathSubmit()}
          />
          <button
            onClick={handleSelectFolder}
            className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm text-white transition-colors"
          >
            Browse
          </button>
        </div>

        {/* 프로젝트 목록 */}
        {projects.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Projects</div>
            {projects.map(p => (
              <button
                key={p.dbPath}
                onClick={() => onSelect(p.dbPath)}
                className="w-full text-left px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-white transition-colors border border-gray-700 hover:border-blue-500"
              >
                {p.name}
              </button>
            ))}
          </div>
        )}

        {rootPath && projects.length === 0 && (
          <p className="text-yellow-500 text-sm">No TaskOps projects found in this folder</p>
        )}
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add taskboard/packages/electron/src/renderer/screens/ProjectSelect.tsx
git commit -m "feat(electron): add ProjectSelect screen with folder browser"
```

---

## Task 16: Electron — Dashboard 화면 (Gantt)

**Files:**
- Create: `taskboard/packages/electron/src/renderer/screens/Dashboard.tsx`

**Step 1: Dashboard.tsx 구현 (frappe-gantt)**

```tsx
// taskboard/packages/electron/src/renderer/screens/Dashboard.tsx
import React, { useEffect, useRef } from 'react'
import Gantt from 'frappe-gantt'
import type { EpicWithTasks, ProjectInfo, TaskStatus } from '@taskboard/core'

const STATUS_COLOR: Record<TaskStatus, string> = {
  done: '#22c55e',
  in_progress: '#eab308',
  todo: '#6b7280',
  interrupted: '#ef4444',
  cancelled: '#374151',
}

interface AllData {
  project: ProjectInfo | undefined
  epics: EpicWithTasks[]
  [key: string]: any
}

interface Props {
  data: AllData | null
}

function buildGanttTasks(epics: EpicWithTasks[]) {
  const tasks: any[] = []
  const now = new Date()

  epics.forEach(({ epic, tasks: epicTasks }) => {
    // Epic 행
    const epicStart = now
    const epicEnd = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
    tasks.push({
      id: epic.id,
      name: `[${epic.id}] ${epic.title}`,
      start: epicStart.toISOString().slice(0, 10),
      end: epicEnd.toISOString().slice(0, 10),
      progress: Math.round(epicTasks.filter(t => t.task.status === 'done').length / Math.max(epicTasks.length, 1) * 100),
      custom_class: `status-${epic.status}`,
    })

    // Task 행
    epicTasks.forEach(({ task }, idx) => {
      const taskStart = new Date(now.getTime() + idx * 2 * 24 * 60 * 60 * 1000)
      const taskEnd = new Date(taskStart.getTime() + 2 * 24 * 60 * 60 * 1000)
      tasks.push({
        id: task.id,
        name: `  ${task.id}: ${task.title}`,
        start: task.created_at.slice(0, 10) || taskStart.toISOString().slice(0, 10),
        end: taskEnd.toISOString().slice(0, 10),
        progress: task.status === 'done' ? 100 : task.status === 'in_progress' ? 50 : 0,
        dependencies: task.id,
        custom_class: `status-${task.status}`,
      })
    })
  })

  return tasks
}

export function Dashboard({ data }: Props) {
  const ganttRef = useRef<HTMLDivElement>(null)
  const ganttInstance = useRef<any>(null)

  const allTasks = data?.epics.flatMap(e => e.tasks.map(t => t.task)) ?? []
  const doneTasks = allTasks.filter(t => t.status === 'done').length
  const inProgressTasks = allTasks.filter(t => t.status === 'in_progress').length

  useEffect(() => {
    if (!ganttRef.current || !data?.epics.length) return

    const ganttTasks = buildGanttTasks(data.epics)
    if (ganttTasks.length === 0) return

    ganttInstance.current = new Gantt(ganttRef.current, ganttTasks, {
      view_mode: 'Week',
      date_format: 'YYYY-MM-DD',
      readonly: true,
    })

    return () => { ganttInstance.current = null }
  }, [data])

  return (
    <div className="p-6 h-full flex flex-col">
      {/* 헤더 요약 */}
      <div className="flex items-center gap-6 mb-6">
        <h1 className="text-xl font-bold text-white">{data?.project?.title}</h1>
        <div className="flex gap-4 text-sm">
          <span className="text-gray-400">Epics: <span className="text-white">{data?.epics.length ?? 0}</span></span>
          <span className="text-gray-400">Tasks: <span className="text-white">{allTasks.length}</span></span>
          <span className="text-green-400">Done: {doneTasks}/{allTasks.length}</span>
          <span className="text-yellow-400">In Progress: {inProgressTasks}</span>
        </div>
      </div>

      {/* Gantt 차트 */}
      <div className="flex-1 bg-gray-900 rounded-xl border border-gray-800 overflow-auto p-4">
        {data?.epics.length ? (
          <div ref={ganttRef} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            No tasks found
          </div>
        )}
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add taskboard/packages/electron/src/renderer/screens/Dashboard.tsx
git commit -m "feat(electron): add Dashboard screen with frappe-gantt visualization"
```

---

## Task 17: Electron — TaskOperations 화면 (ReactFlow)

**Files:**
- Create: `taskboard/packages/electron/src/renderer/screens/TaskOperations.tsx`
- Create: `taskboard/packages/electron/src/renderer/components/HierarchyBar.tsx`

**Step 1: HierarchyBar.tsx (상단 계층 바 + 팝업)**

```tsx
// taskboard/packages/electron/src/renderer/components/HierarchyBar.tsx
import React, { useState } from 'react'
import type { Task, EpicWithTasks } from '@taskboard/core'

interface Props {
  selectedTask: Task | undefined
  epics: EpicWithTasks[]
  onSelectTask: (id: string) => void
}

export function HierarchyBar({ selectedTask, epics, onSelectTask }: Props) {
  const [open, setOpen] = useState(false)

  // 부모 찾기
  const findParent = (taskId: string): Task | undefined => {
    for (const { epic, tasks } of epics) {
      if (tasks.some(t => t.task.id === taskId)) return epic
      for (const { task, children } of tasks) {
        if (children.some(c => c.id === taskId)) return task
      }
    }
    return undefined
  }

  // 자식 찾기
  const findChildren = (taskId: string): Task[] => {
    for (const { tasks } of epics) {
      const found = tasks.find(t => t.task.id === taskId)
      if (found) return found.children
    }
    return []
  }

  const parent = selectedTask ? findParent(selectedTask.id) : undefined
  const children = selectedTask ? findChildren(selectedTask.id) : []

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-white border border-gray-700 transition-colors"
      >
        {parent && <span className="text-gray-400">{parent.id}</span>}
        {parent && <span className="text-gray-600">›</span>}
        {selectedTask
          ? <span className="font-medium">[{selectedTask.id}] {selectedTask.title}</span>
          : <span className="text-gray-400">Select a task</span>
        }
        <span className="text-gray-400 ml-1">▼</span>
      </button>

      {open && selectedTask && (
        <div className="absolute top-full left-0 mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 min-w-64 p-2">
          {parent && (
            <button
              onClick={() => { onSelectTask(parent.id); setOpen(false) }}
              className="w-full text-left px-3 py-1.5 hover:bg-gray-700 rounded text-sm text-gray-300 flex items-center gap-2"
            >
              <span className="text-gray-500">↑</span> {parent.id}: {parent.title}
            </button>
          )}
          <div className="px-3 py-1.5 bg-blue-600/20 rounded text-sm text-white border border-blue-500/30 my-1">
            ▶ [{selectedTask.id}] {selectedTask.title}
          </div>
          {children.map(child => (
            <button
              key={child.id}
              onClick={() => { onSelectTask(child.id); setOpen(false) }}
              className="w-full text-left px-3 py-1.5 hover:bg-gray-700 rounded text-sm text-gray-300 flex items-center gap-2 ml-4"
            >
              <span className="text-gray-500">↓</span> {child.id}: {child.title}
            </button>
          ))}
          {children.length === 0 && (
            <div className="px-3 py-1 text-xs text-gray-500">No subtasks</div>
          )}
        </div>
      )}
    </div>
  )
}
```

**Step 2: TaskOperations.tsx 구현 (ReactFlow)**

```tsx
// taskboard/packages/electron/src/renderer/screens/TaskOperations.tsx
import React, { useMemo } from 'react'
import ReactFlow, {
  Node, Edge, Background, Controls,
  MarkerType, Position
} from 'reactflow'
import 'reactflow/dist/style.css'
import { HierarchyBar } from '../components/HierarchyBar'
import type { Operation, Task, EpicWithTasks } from '@taskboard/core'

const OP_COLOR: Record<string, string> = {
  start: '#3b82f6',
  progress: '#6b7280',
  complete: '#22c55e',
  error: '#ef4444',
  interrupt: '#eab308',
}

function buildFlowNodes(operations: Operation[]): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = operations.map((op, idx) => ({
    id: String(op.id),
    position: { x: 250, y: idx * 120 },
    data: {
      label: (
        <div style={{ textAlign: 'center', fontSize: '12px' }}>
          <div style={{ fontWeight: 'bold', color: OP_COLOR[op.operation_type] }}>
            {op.operation_type.toUpperCase()}
          </div>
          <div style={{ color: '#9ca3af', fontSize: '11px' }}>
            {op.created_at?.slice(11, 16) ?? ''}
          </div>
          {op.summary && (
            <div style={{ color: '#d1d5db', fontSize: '11px', maxWidth: '160px', whiteSpace: 'normal' }}>
              {op.summary}
            </div>
          )}
        </div>
      )
    },
    style: {
      background: '#1f2937',
      border: `1px solid ${OP_COLOR[op.operation_type]}`,
      borderRadius: '8px',
      padding: '8px 16px',
      minWidth: '180px',
    },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  }))

  const edges: Edge[] = operations.slice(0, -1).map((op, idx) => ({
    id: `e${op.id}-${operations[idx + 1].id}`,
    source: String(op.id),
    target: String(operations[idx + 1].id),
    markerEnd: { type: MarkerType.ArrowClosed, color: '#4b5563' },
    style: { stroke: '#4b5563' },
  }))

  return { nodes, edges }
}

interface AllData {
  epics: EpicWithTasks[]
  operations: Operation[]
  [key: string]: any
}

interface Props {
  data: AllData | null
  selectedTaskId: string | null
  setSelectedTask: (id: string | null) => void
}

export function TaskOperations({ data, selectedTaskId, setSelectedTask }: Props) {
  const allTasks = data?.epics.flatMap(e =>
    e.tasks.flatMap(t => [t.task, ...t.children])
  ) ?? []

  const selectedTask = allTasks.find(t => t.id === selectedTaskId) ?? allTasks[0]

  const taskOps = useMemo(() => {
    if (!selectedTask || !data) return []
    return data.operations.filter(o => o.task_id === selectedTask.id)
  }, [selectedTask, data])

  const { nodes, edges } = useMemo(() => buildFlowNodes(taskOps), [taskOps])

  return (
    <div className="p-6 h-full flex flex-col">
      {/* 상단 계층 바 */}
      <div className="mb-4">
        <HierarchyBar
          selectedTask={selectedTask}
          epics={data?.epics ?? []}
          onSelectTask={setSelectedTask}
        />
      </div>

      {/* ReactFlow */}
      <div className="flex-1 bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        {taskOps.length > 0 ? (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#374151" gap={16} />
            <Controls />
          </ReactFlow>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            {selectedTask ? 'No operations recorded for this task' : 'Select a task to view operations'}
          </div>
        )}
      </div>
    </div>
  )
}
```

**Step 3: Commit**

```bash
git add taskboard/packages/electron/src/renderer/screens/TaskOperations.tsx taskboard/packages/electron/src/renderer/components/HierarchyBar.tsx
git commit -m "feat(electron): add TaskOperations screen with ReactFlow diagram and hierarchy bar"
```

---

## Task 18: Electron — Resources 화면

**Files:**
- Create: `taskboard/packages/electron/src/renderer/screens/Resources.tsx`

**Step 1: Resources.tsx 구현**

```tsx
// taskboard/packages/electron/src/renderer/screens/Resources.tsx
import React from 'react'
import type { Resource } from '@taskboard/core'

const TYPE_BADGE: Record<string, string> = {
  input: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  output: 'bg-green-500/20 text-green-400 border-green-500/30',
  reference: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  intermediate: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
}

interface Props {
  resources: Resource[]
}

export function Resources({ resources }: Props) {
  return (
    <div className="p-6">
      <h2 className="text-xl font-bold text-white mb-4">Resources ({resources.length})</h2>
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wider">
              <th className="text-left px-4 py-3">Type</th>
              <th className="text-left px-4 py-3">Task</th>
              <th className="text-left px-4 py-3">File Path</th>
              <th className="text-left px-4 py-3">Description</th>
              <th className="text-left px-4 py-3">Date</th>
            </tr>
          </thead>
          <tbody>
            {resources.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">No resources recorded</td></tr>
            )}
            {resources.map(r => (
              <tr key={r.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded border text-xs ${TYPE_BADGE[r.res_type]}`}>
                    {r.res_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-400 font-mono text-xs">{r.task_id}</td>
                <td className="px-4 py-3 text-gray-200 font-mono text-xs">{r.file_path}</td>
                <td className="px-4 py-3 text-gray-400">{r.description ?? '—'}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">{r.created_at.slice(0, 10)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add taskboard/packages/electron/src/renderer/screens/Resources.tsx
git commit -m "feat(electron): add Resources screen with table view"
```

---

## Task 19: Electron — Settings 화면

**Files:**
- Create: `taskboard/packages/electron/src/renderer/screens/Settings.tsx`

**Step 1: Settings.tsx 구현**

```tsx
// taskboard/packages/electron/src/renderer/screens/Settings.tsx
import React from 'react'
import type { Setting } from '@taskboard/core'

interface Props {
  settings: Setting[]
}

export function Settings({ settings }: Props) {
  return (
    <div className="p-6">
      <h2 className="text-xl font-bold text-white mb-4">Settings</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {settings.length === 0 && (
          <div className="col-span-3 text-center text-gray-500 py-12">No settings found</div>
        )}
        {settings.map(s => (
          <div
            key={s.key}
            className="bg-gray-900 rounded-xl border border-gray-800 p-4 hover:border-gray-700 transition-colors"
          >
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">{s.key}</div>
            <div className="text-lg font-semibold text-yellow-400">{s.value}</div>
            {s.description && (
              <div className="text-xs text-gray-500 mt-2">{s.description}</div>
            )}
            <div className="text-xs text-gray-600 mt-2">Updated: {s.updated_at.slice(0, 10)}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

**Step 2: Electron 전체 빌드 확인**

```bash
cd taskboard && pnpm --filter @taskboard/electron build
```

Expected: `dist/` 생성, 오류 없음

**Step 3: Electron 수동 테스트**

```bash
cd taskboard && pnpm dev:electron
```

Expected: Electron 앱 실행, ProjectSelect 화면 표시

**Step 4: Commit**

```bash
git add taskboard/packages/electron/src/renderer/screens/Settings.tsx
git commit -m "feat(electron): add Settings screen, complete Electron implementation"
```

---

## Task 20: Electron — E2E 테스트 (Playwright)

**Files:**
- Create: `taskboard/packages/electron/tests/e2e/app.spec.ts`
- Create: `taskboard/packages/electron/playwright.config.ts`

**Step 1: Playwright Electron 설정**

```typescript
// taskboard/packages/electron/playwright.config.ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: 'tests/e2e',
  timeout: 30000,
  use: {
    // Electron E2E는 electron-playwright-helpers 또는 직접 launch 사용
  },
})
```

**Step 2: E2E 테스트 작성**

```typescript
// taskboard/packages/electron/tests/e2e/app.spec.ts
import { test, expect, _electron as electron } from '@playwright/test'
import path from 'path'

test.describe('TaskBoard Electron', () => {
  test('앱이 실행되고 ProjectSelect 화면을 표시한다', async () => {
    const app = await electron.launch({
      args: [path.join(__dirname, '../../dist/main/index.js')],
    })
    const page = await app.firstWindow()

    await expect(page.locator('text=TaskBoard')).toBeVisible()
    await expect(page.locator('input[placeholder*="path"]')).toBeVisible()

    await app.close()
  })

  test('픽스처 DB로 Dashboard를 표시한다', async () => {
    const fixtureRoot = path.join(__dirname, '../../../../fixtures')
    const app = await electron.launch({
      args: [path.join(__dirname, '../../dist/main/index.js'), '--path', fixtureRoot],
    })
    const page = await app.firstWindow()

    // 프로젝트 선택
    await page.locator('text=fixture').click()

    // Dashboard 화면 확인
    await expect(page.locator('text=Dashboard')).toBeVisible()

    await app.close()
  })
})
```

**Step 3: E2E 테스트 실행**

```bash
cd taskboard && pnpm --filter @taskboard/electron test:e2e
```

Expected: PASS (앱 실행 및 화면 전환 확인)

**Step 4: Commit**

```bash
git add taskboard/packages/electron/tests/e2e/ taskboard/packages/electron/playwright.config.ts
git commit -m "test(electron): add Playwright E2E tests for app launch and navigation"
```

---

## Task 21: 패키징 & npx 실행 설정

**Files:**
- Modify: `taskboard/packages/tui/package.json`
- Modify: `taskboard/packages/electron/package.json`
- Create: `taskboard/packages/electron/electron-builder.config.js`

**Step 1: TUI bin 설정 확인**

`packages/tui/package.json`의 `bin` 필드가 `dist/index.js`를 가리키고 있는지 확인.
`dist/index.js` 첫 줄에 shebang이 있는지 확인: `#!/usr/bin/env node`

**Step 2: electron-builder 설정**

```javascript
// taskboard/packages/electron/electron-builder.config.js
module.exports = {
  appId: 'com.taskops.taskboard',
  productName: 'TaskBoard',
  directories: { output: 'release' },
  files: ['dist/**/*'],
  mac: { target: 'dmg' },
  win: { target: 'nsis' },
  linux: { target: 'AppImage' },
}
```

**Step 3: 전체 빌드 테스트**

```bash
cd taskboard && pnpm build
```

Expected: core, tui, electron 모두 빌드 성공

**Step 4: TUI npx 테스트**

```bash
# 로컬에서 npx 흉내
cd taskboard && node packages/tui/dist/index.js --help
```

Expected: 도움말 출력

**Step 5: 전체 테스트 실행**

```bash
cd taskboard && pnpm test
```

Expected: 모든 테스트 PASS

**Step 6: 최종 Commit**

```bash
git add taskboard/
git commit -m "chore(taskboard): add packaging config and finalize build setup"
```

---

## 완료 기준

- [ ] `pnpm test` — 모든 유닛/컴포넌트 테스트 통과
- [ ] `pnpm dev:tui` — TUI 실행, 4개 화면 Tab 전환 작동
- [ ] `pnpm dev:electron` — Electron 앱 실행, 4개 화면 사이드바 전환 작동
- [ ] Electron Dashboard Gantt 차트 렌더링 확인
- [ ] Electron TaskOperations ReactFlow 노드 표시 확인
- [ ] DB 변경 시 양쪽 앱 자동 갱신 확인
- [ ] Playwright E2E 테스트 통과
