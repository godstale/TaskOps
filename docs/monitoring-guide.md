# TaskOps Monitoring Data Collection Guide

**대상:** TaskBoard-CLI / TaskBoard-Electron 개발자
**버전:** TaskOps v0.2.6+ (DB Schema v6, agent_events는 v7 예정)

---

## 1. Overview

TaskOps는 두 가지 데이터 소스에서 모니터링 데이터를 제공합니다.

```
┌─────────────────────────────────────────────────────────┐
│  taskops.db (SQLite)                                    │
│  ├── operations     ← [우선순위 1] 에이전트 작업 로그    │
│  ├── agent_events   ← [우선순위 2] 도구 사용/토큰 (예정) │
│  ├── tasks          ← 워크플로우/태스크 상태             │
│  └── workflows      ← 작업 계획 목록                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  파일시스템                                              │
│  ├── %USERPROFILE%\.claude\projects\<hash>\*.jsonl      │
│  │   ← [우선순위 3] Claude Code 세션 이벤트 raw 데이터  │
│  └── ~/.gemini/tmp/<hash>/chats\*.json                  │
│      ← [우선순위 4] Gemini CLI 세션 데이터              │
└─────────────────────────────────────────────────────────┘
```

### 데이터 소스 우선순위 요약

| 우선순위 | 소스 | 내용 | 구현 상태 |
|---------|------|------|----------|
| 1 | `operations` 테이블 | start/progress/complete/error 로그 | ✅ 사용 가능 |
| 2 | `agent_events` 테이블 | 도구 호출, 토큰 사용량, thinking | ⏳ v7 구현 예정 |
| 3 | Claude Code JSONL | 세션 raw 이벤트 스트림 | ✅ 사용 가능 |
| 4 | Gemini CLI JSON | Gemini 세션 이벤트 | ✅ 사용 가능 |

---

## 2. SQLite DB 직접 접근

### DB 파일 위치

`taskops.db`는 사용자가 `python -m cli init` 을 실행한 프로젝트 디렉토리에 생성됩니다.

```
<project-root>/
└── taskops.db
```

TaskBoard 앱은 DB 경로를 사용자 설정으로 받거나, 현재 디렉토리에서 탐색합니다.

### 연결 방법

**Node.js / Electron (`better-sqlite3` 권장)**

```javascript
const Database = require('better-sqlite3');

// DB 연결 (read-only로 열기 — 앱이 DB를 수정하지 않도록)
const db = new Database('/path/to/taskops.db', { readonly: true });

// WAL 모드 확인 (TaskOps는 WAL 사용 — 읽기 중 쓰기 잠금 없음)
const { journal_mode } = db.pragma('journal_mode', { simple: true });
```

> **중요:** TaskBoard 앱은 DB를 `readonly` 모드로만 열어야 합니다.
> TaskOps 에이전트가 동시에 쓰기 작업 중일 수 있으므로 WAL 모드 덕분에 읽기는 항상 안전합니다.

### 스키마 버전 확인

```javascript
const row = db.prepare(
  "SELECT value FROM settings WHERE workflow_id='' AND key='__schema_version'"
).get();
const schemaVersion = parseInt(row?.value ?? '0');

// agent_events 테이블은 v7부터 사용 가능
const hasAgentEvents = schemaVersion >= 7;
```

---

## 3. [우선순위 1] operations 테이블

에이전트가 태스크를 수행하며 기록하는 작업 로그입니다. 실시간 진행 상황 모니터링의 핵심 데이터 소스입니다.

### 테이블 구조

```sql
CREATE TABLE operations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT NOT NULL,          -- 연결된 태스크 ID (예: PRJ-T001)
    operation_type  TEXT NOT NULL,          -- 'start'|'progress'|'complete'|'error'|'interrupt'
    agent_platform  TEXT,                   -- 'claude_code'|'gemini_cli' 등
    workflow_id     TEXT,                   -- 연결된 워크플로우 ID (예: PRJ-WF)
    summary         TEXT,                   -- 사람이 읽을 수 있는 요약
    details         TEXT,                   -- 상세 정보 (JSON 문자열 가능)
    subagent_used   INTEGER DEFAULT 0,      -- 서브에이전트 사용 여부 (0/1)
    subagent_result TEXT,                   -- 서브에이전트 결과 요약
    started_at      TEXT,                   -- ISO8601 타임스탬프
    completed_at    TEXT,                   -- ISO8601 타임스탬프
    tool_name       TEXT,                   -- 사용된 도구명 (Edit, Bash 등)
    skill_name      TEXT,                   -- 활성 스킬명
    input_tokens    INTEGER,                -- 입력 토큰 수
    output_tokens   INTEGER,                -- 출력 토큰 수
    duration_seconds INTEGER,              -- 작업 소요 시간
    created_at      TEXT NOT NULL           -- 기록 생성 시각
);
```

### operation_type 의미

| 타입 | 의미 |
|------|------|
| `start` | 태스크 작업 시작 |
| `progress` | 중간 진행 단계 완료 |
| `complete` | 태스크 완료 |
| `error` | 블로킹 오류 발생 |
| `interrupt` | 작업 일시 중단 |

### 주요 쿼리 예시

**워크플로우별 최근 작업 로그 (실시간 피드용)**

```sql
SELECT
    o.id,
    o.task_id,
    t.title        AS task_title,
    o.operation_type,
    o.summary,
    o.agent_platform,
    o.tool_name,
    o.created_at
FROM operations o
JOIN tasks t ON t.id = o.task_id
WHERE o.workflow_id = ?          -- 워크플로우 ID 바인딩
ORDER BY o.id DESC
LIMIT 50;
```

**태스크별 진행 상태 요약**

```sql
SELECT
    t.id,
    t.title,
    t.status,
    t.type,
    COUNT(o.id)                         AS op_count,
    MAX(o.created_at)                   AS last_activity,
    SUM(CASE WHEN o.operation_type = 'error' THEN 1 ELSE 0 END) AS error_count
FROM tasks t
LEFT JOIN operations o ON o.task_id = t.id
WHERE t.workflow_id = ?
  AND t.type IN ('epic', 'task')
GROUP BY t.id
ORDER BY t.seq_order;
```

**현재 진행 중인 태스크**

```sql
SELECT
    t.id,
    t.title,
    t.type,
    o.summary      AS latest_summary,
    o.agent_platform,
    o.created_at   AS last_updated
FROM tasks t
JOIN operations o ON o.id = (
    SELECT id FROM operations
    WHERE task_id = t.id
    ORDER BY id DESC LIMIT 1
)
WHERE t.status = 'in_progress'
  AND t.workflow_id = ?
ORDER BY o.id DESC;
```

**워크플로우 전체 진행률**

```sql
SELECT
    w.id,
    w.title,
    COUNT(CASE WHEN t.type = 'task' THEN 1 END)                          AS total_tasks,
    COUNT(CASE WHEN t.type = 'task' AND t.status = 'done' THEN 1 END)   AS done_tasks,
    COUNT(CASE WHEN t.type = 'task' AND t.status = 'in_progress' THEN 1 END) AS active_tasks
FROM workflows w
LEFT JOIN tasks t ON t.workflow_id = w.id
WHERE w.id = ?
GROUP BY w.id;
```

### 실시간 폴링 패턴

```javascript
// 마지막으로 읽은 operation ID를 추적해 새 항목만 가져옴
let lastSeenId = 0;

const poll = db.prepare(`
    SELECT o.*, t.title AS task_title
    FROM operations o
    JOIN tasks t ON t.id = o.task_id
    WHERE o.id > ?
    ORDER BY o.id ASC
    LIMIT 100
`);

function pollOperations() {
    const rows = poll.all(lastSeenId);
    if (rows.length > 0) {
        lastSeenId = rows[rows.length - 1].id;
        // 새 이벤트 처리
        rows.forEach(row => handleNewOperation(row));
    }
}

// 권장 폴링 간격: 2~3초
setInterval(pollOperations, 2500);
```

---

## 4. [우선순위 2] agent_events 테이블 *(⏳ v7 구현 예정)*

> **현재 상태:** `agent_events` 테이블은 Schema v7에서 추가 예정입니다.
> 앱 구현 시 `schemaVersion >= 7` 체크 후 기능을 활성화하세요.

에이전트의 도구 호출 단위 이벤트를 기록합니다. JSONL 파싱 또는 PostToolUse 훅을 통해 채워집니다.

### 테이블 구조 (예정)

```sql
CREATE TABLE agent_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT,           -- Claude Code 세션 해시
    workflow_id     TEXT,           -- 연결된 워크플로우 ID
    task_id         TEXT,           -- 이벤트 발생 시점의 활성 태스크
    event_type      TEXT NOT NULL,  -- 'tool_use'|'tool_result'|'thinking'|'subagent_start'|'subagent_end'
    tool_name       TEXT,           -- Edit, Bash, Grep 등 (thinking 이벤트는 NULL)
    skill_name      TEXT,           -- 활성 스킬명
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    thinking_tokens INTEGER,        -- JSONL 파싱 시에만 채워짐
    duration_ms     INTEGER,        -- tool_use ~ tool_result 소요 시간
    event_timestamp TEXT,           -- 원본 타임스탬프
    source          TEXT,           -- 'hook'|'jsonl'
    created_at      TEXT NOT NULL
);
```

### 주요 쿼리 예시 (v7 이후)

**워크플로우별 도구 사용 패턴**

```sql
SELECT
    tool_name,
    COUNT(*)                    AS call_count,
    AVG(duration_ms)            AS avg_duration_ms,
    ROUND(COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 1) AS pct
FROM agent_events
WHERE workflow_id = ?
  AND event_type = 'tool_use'
GROUP BY tool_name
ORDER BY call_count DESC;
```

**세션별 토큰 사용량 집계**

```sql
SELECT
    session_id,
    SUM(input_tokens)    AS total_input,
    SUM(output_tokens)   AS total_output,
    SUM(thinking_tokens) AS total_thinking,
    COUNT(CASE WHEN event_type = 'thinking' THEN 1 END) AS thinking_events
FROM agent_events
WHERE session_id = ?
  AND source = 'jsonl'   -- JSONL 파싱 데이터에만 토큰 정보 있음
GROUP BY session_id;
```

**가용성 체크 후 조건부 사용 패턴**

```javascript
function getAgentEventStats(workflowId) {
    if (!hasAgentEvents) {
        // v7 미만이면 operations 테이블로 대체 표시
        return { available: false, fallback: 'operations' };
    }
    const rows = db.prepare(`
        SELECT tool_name, COUNT(*) AS count, AVG(duration_ms) AS avg_ms
        FROM agent_events
        WHERE workflow_id = ? AND event_type = 'tool_use'
        GROUP BY tool_name ORDER BY count DESC
    `).all(workflowId);
    return { available: true, data: rows };
}
```

---

## 5. [우선순위 3] Claude Code JSONL 파싱

TaskOps `agent_events` 테이블이 아직 없을 때, 또는 더 세밀한 raw 이벤트가 필요할 때 직접 파싱합니다.

### 파일 위치

```
Windows: %USERPROFILE%\.claude\projects\<project-hash>\
  ├── <session-id>.jsonl        ← 세션 이벤트 스트림
  └── sessions-index.json       ← 세션 메타데이터 (토큰 수, git branch 등)

macOS/Linux: ~/.claude/projects/<project-hash>/
```

### 프로젝트 해시 산출

Claude Code는 프로젝트 절대 경로를 해시화해 디렉토리명으로 사용합니다.

```javascript
const crypto = require('crypto');
const path = require('path');
const os = require('os');
const fs = require('fs');

/**
 * 프로젝트 경로로 Claude Code 세션 디렉토리를 찾습니다.
 * Claude Code의 정확한 해시 알고리즘이 공개되지 않았으므로,
 * 디렉토리 목록을 스캔해 sessions-index.json의 경로 정보로 매칭합니다.
 */
function findClaudeProjectDir(projectAbsPath) {
    const claudeBase = path.join(os.homedir(), '.claude', 'projects');
    if (!fs.existsSync(claudeBase)) return null;

    for (const hashDir of fs.readdirSync(claudeBase)) {
        const indexPath = path.join(claudeBase, hashDir, 'sessions-index.json');
        if (!fs.existsSync(indexPath)) continue;
        try {
            const index = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
            // sessions-index.json에 cwd 또는 projectPath 필드가 있으면 비교
            const entries = Array.isArray(index) ? index : Object.values(index);
            const match = entries.some(e =>
                e?.cwd === projectAbsPath || e?.projectPath === projectAbsPath
            );
            if (match) return path.join(claudeBase, hashDir);
        } catch { /* 파싱 실패 시 건너뜀 */ }
    }
    return null;
}
```

> **대안:** TaskOps CLI의 `monitor parse --auto` 명령이 자동으로 올바른 디렉토리를 찾아 `agent_events`에 저장합니다. v7 이후에는 직접 파싱 대신 DB를 읽는 방식을 권장합니다.

### JSONL 파일 구조

각 줄이 독립 JSON 이벤트입니다.

```jsonl
{"type":"tool_use","id":"toolu_01Abc","name":"Edit","input":{"file_path":"..."},"timestamp":"2026-03-22T10:30:00Z"}
{"type":"tool_result","tool_use_id":"toolu_01Abc","content":"...","timestamp":"2026-03-22T10:30:01Z"}
{"type":"thinking","thinking":"...","thinking_tokens":320,"timestamp":"2026-03-22T10:30:00Z"}
```

주요 이벤트 타입:

| 타입 | 설명 | 주요 필드 |
|------|------|----------|
| `tool_use` | 도구 호출 시작 | `id`, `name`, `input`, `timestamp` |
| `tool_result` | 도구 호출 결과 | `tool_use_id`, `content`, `timestamp` |
| `thinking` | 모델 thinking 블록 | `thinking`, `thinking_tokens`, `timestamp` |

### JSONL 파싱 예시

```javascript
const readline = require('readline');

async function parseSessionJsonl(filePath) {
    const events = [];
    const toolUseMap = new Map(); // id → tool_use 이벤트

    const rl = readline.createInterface({
        input: fs.createReadStream(filePath, { encoding: 'utf8' })
    });

    for await (const line of rl) {
        if (!line.trim()) continue;
        let event;
        try { event = JSON.parse(line); } catch { continue; }

        if (event.type === 'tool_use') {
            toolUseMap.set(event.id, event);
            events.push({ ...event, duration_ms: null });

        } else if (event.type === 'tool_result') {
            const use = toolUseMap.get(event.tool_use_id);
            if (use) {
                const duration = new Date(event.timestamp) - new Date(use.timestamp);
                // tool_use 이벤트에 duration 보정
                const idx = events.findIndex(e => e.id === use.id);
                if (idx >= 0) events[idx].duration_ms = duration;
            }

        } else if (event.type === 'thinking') {
            events.push(event);
        }
    }

    return events;
}
```

### 실시간 파일 감시 (Electron)

```javascript
const chokidar = require('chokidar'); // 또는 fs.watch

let fileOffset = 0; // 마지막으로 읽은 바이트 위치

function watchJsonlFile(filePath, onEvent) {
    const watcher = chokidar.watch(filePath, { usePolling: false });

    watcher.on('change', () => {
        const stat = fs.statSync(filePath);
        if (stat.size <= fileOffset) return;

        const buf = Buffer.alloc(stat.size - fileOffset);
        const fd = fs.openSync(filePath, 'r');
        fs.readSync(fd, buf, 0, buf.length, fileOffset);
        fs.closeSync(fd);
        fileOffset = stat.size;

        buf.toString('utf8').split('\n').forEach(line => {
            if (!line.trim()) return;
            try { onEvent(JSON.parse(line)); } catch { /* skip */ }
        });
    });

    return watcher;
}
```

### 실시간 파일 감시 (CLI — polling)

```javascript
function watchJsonlFileCli(filePath, onEvent, intervalMs = 1000) {
    let fileOffset = 0;

    return setInterval(() => {
        try {
            const stat = fs.statSync(filePath);
            if (stat.size <= fileOffset) return;

            const buf = Buffer.alloc(stat.size - fileOffset);
            const fd = fs.openSync(filePath, 'r');
            fs.readSync(fd, buf, 0, buf.length, fileOffset);
            fs.closeSync(fd);
            fileOffset = stat.size;

            buf.toString('utf8').split('\n').forEach(line => {
                if (!line.trim()) return;
                try { onEvent(JSON.parse(line)); } catch { /* skip */ }
            });
        } catch { /* 파일 없음 또는 접근 불가 — 조용히 건너뜀 */ }
    }, intervalMs);
}
```

---

## 6. [우선순위 4] Gemini CLI 세션 파일

### 파일 위치

```
macOS/Linux: ~/.gemini/tmp/<project-hash>/chats/
Windows:     %USERPROFILE%\.gemini\tmp\<project-hash>\chats\

파일명 패턴: session-2026-03-22T10-45-3b44bc68.json
```

### 파일 구조

Claude Code JSONL과 달리 단일 JSON 파일입니다.

```json
{
  "sessionId": "3b44bc68",
  "createdAt": "2026-03-22T10:45:00Z",
  "messages": [
    {
      "role": "user",
      "parts": [{ "text": "..." }],
      "timestamp": "2026-03-22T10:45:01Z"
    },
    {
      "role": "model",
      "parts": [
        { "text": "..." },
        {
          "functionCall": {
            "name": "edit_file",
            "args": { "path": "...", "content": "..." }
          }
        }
      ],
      "usageMetadata": {
        "promptTokenCount": 1200,
        "candidatesTokenCount": 340,
        "totalTokenCount": 1540
      },
      "timestamp": "2026-03-22T10:45:03Z"
    }
  ]
}
```

### 파싱 예시

```javascript
function parseGeminiSession(filePath) {
    const session = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const events = [];

    for (const msg of session.messages ?? []) {
        if (msg.role !== 'model') continue;

        // 토큰 정보
        const tokens = msg.usageMetadata ?? {};

        // 도구 호출 추출
        for (const part of msg.parts ?? []) {
            if (part.functionCall) {
                events.push({
                    type: 'tool_use',
                    tool_name: part.functionCall.name,
                    input: part.functionCall.args,
                    input_tokens: tokens.promptTokenCount ?? null,
                    output_tokens: tokens.candidatesTokenCount ?? null,
                    timestamp: msg.timestamp,
                });
            }
        }
    }

    return events;
}
```

### OpenTelemetry 로컬 수집 (선택)

Gemini CLI의 상세 텔레메트리를 로컬 파일로 수집하려면:

```bash
gemini --telemetry-target=local --telemetry-outfile=taskops_telemetry.json
```

이 파일은 기능 사용 빈도, 지연 시간 등 OpenTelemetry 형식의 구조화된 데이터를 포함합니다.

---

## 7. 실시간 업데이트 패턴

### 권장 폴링 간격

| 데이터 소스 | 권장 간격 | 이유 |
|------------|----------|------|
| `operations` 테이블 | 2~3초 | 에이전트 활동 단위 반영 |
| `agent_events` 테이블 | 3~5초 | 도구 호출 단위 (더 빈번함) |
| JSONL 파일 (CLI) | 1~2초 | tail 방식으로 경량 |
| JSONL 파일 (Electron) | `fs.watch` 이벤트 | 변경 시에만 반응 |

### Electron IPC 브릿지 패턴

메인 프로세스가 DB를 읽어 렌더러(UI)로 전달하는 패턴:

```javascript
// main.js (메인 프로세스)
const { ipcMain } = require('electron');

ipcMain.handle('get-operations', async (event, { workflowId, afterId }) => {
    return db.prepare(`
        SELECT o.*, t.title AS task_title
        FROM operations o JOIN tasks t ON t.id = o.task_id
        WHERE o.workflow_id = ? AND o.id > ?
        ORDER BY o.id ASC LIMIT 100
    `).all(workflowId, afterId);
});

// 주기적 폴링 후 렌더러에 push
let lastId = 0;
setInterval(() => {
    const rows = db.prepare(
        'SELECT * FROM operations WHERE id > ? ORDER BY id ASC LIMIT 100'
    ).all(lastId);
    if (rows.length > 0) {
        lastId = rows[rows.length - 1].id;
        mainWindow.webContents.send('new-operations', rows);
    }
}, 2500);
```

```javascript
// renderer.js (렌더러 프로세스)
const { ipcRenderer } = require('electron');

ipcRenderer.on('new-operations', (event, rows) => {
    rows.forEach(row => appendToActivityFeed(row));
});
```

### 연결 오류 처리

```javascript
function createDbConnection(dbPath) {
    try {
        const db = new Database(dbPath, { readonly: true });
        // WAL 체크포인트가 읽기를 차단하지 않도록 설정
        db.pragma('busy_timeout = 3000');
        return db;
    } catch (err) {
        // DB 파일이 없거나 잠긴 경우 — 재시도 또는 사용자에게 알림
        console.error('[TaskBoard] DB 연결 실패:', err.message);
        return null;
    }
}
```

---

## 부록 A: 테이블 관계 다이어그램

```
workflows
  │  id, title, status, description
  │
  ├──< tasks (type='epic')
  │     │  id, title, status, workflow_id
  │     │
  │     └──< tasks (type='task')
  │           │  id, title, status, parent_id, workflow_id
  │           │
  │           ├──< operations
  │           │     id, task_id, operation_type, summary, created_at
  │           │
  │           ├──< agent_events  [v7 예정]
  │           │     id, task_id, event_type, tool_name, duration_ms
  │           │
  │           └──< resources
  │                 id, task_id, file_path, res_type
  │
  └──< agent_events (workflow_id로 직접 연결)  [v7 예정]
```

---

## 부록 B: 빠른 시작 체크리스트

TaskBoard 앱 초기 연결 시 확인 순서:

1. `taskops.db` 파일 존재 여부 확인
2. `readonly` 모드로 DB 연결
3. `settings` 테이블에서 `__schema_version` 조회 → 버전 분기 처리
4. `workflows` 테이블에서 활성 워크플로우 목록 로드
5. `operations` 테이블 폴링 시작 (우선순위 1)
6. `schemaVersion >= 7`이면 `agent_events` 폴링 추가 (우선순위 2)
7. Claude Code 프로젝트 디렉토리 탐색 → JSONL 감시 시작 (우선순위 3)
8. Gemini CLI 세션 디렉토리 탐색 → JSON 파싱 (우선순위 4)
