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
