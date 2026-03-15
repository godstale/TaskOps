/**
 * 테스트용 샘플 DB 생성 스크립트.
 * 실행: node create-fixture.js
 * 결과: fixture.db 생성
 */
const Database = require('better-sqlite3')
const path = require('path')

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
