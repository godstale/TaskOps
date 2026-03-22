"""SQLite schema definition for TaskOps.
TaskOps DB 스키마 정의 모듈.
"""

SCHEMA_VERSION = 3

SQL_CREATE_TASKS = """
CREATE TABLE IF NOT EXISTS tasks (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL,
    type        TEXT NOT NULL CHECK(type IN ('project','epic','task','objective')),
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'todo'
                CHECK(status IN ('todo','in_progress','interrupted','done','cancelled')),
    parent_id   TEXT,
    todo        TEXT,
    interrupt   TEXT,
    milestone_target TEXT,
    due_date    TEXT,
    seq_order   INTEGER,
    parallel_group TEXT,
    depends_on  TEXT,
    workflow_id TEXT,                      -- references workflows(id), nullable (v3+)
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

SQL_CREATE_WORKFLOWS = """
CREATE TABLE IF NOT EXISTS workflows (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL,
    title       TEXT NOT NULL,
    source_file TEXT,
    status      TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active','completed','archived')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES tasks(id)
);
"""

SQL_CREATE_OPERATIONS = """
CREATE TABLE IF NOT EXISTS operations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT NOT NULL,
    operation_type  TEXT NOT NULL
                    CHECK(operation_type IN ('start','progress','complete','error','interrupt')),
    agent_platform  TEXT,
    workflow_id     TEXT,                      -- references workflows(id), nullable (v3+)
    summary         TEXT,
    details         TEXT,
    subagent_used   INTEGER DEFAULT 0,
    subagent_result TEXT,
    started_at      TEXT,
    completed_at    TEXT,
    tool_name       TEXT,
    skill_name      TEXT,
    mcp_name        TEXT,
    retry_count     INTEGER DEFAULT 0,
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    duration_seconds INTEGER,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
"""

SQL_CREATE_RESOURCES = """
CREATE TABLE IF NOT EXISTS resources (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    description TEXT,
    res_type    TEXT NOT NULL DEFAULT 'reference'
                CHECK(res_type IN ('input','output','reference','intermediate')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
"""

SQL_CREATE_SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    description TEXT,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

SQL_CREATE_CHECKPOINTS = """
CREATE TABLE IF NOT EXISTS checkpoints (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    note        TEXT,
    snapshot    TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

SQL_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_tasks_project   ON tasks(project_id);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_parent    ON tasks(parent_id);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_type      ON tasks(type);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_status    ON tasks(status);",
    "CREATE INDEX IF NOT EXISTS idx_operations_task ON operations(task_id);",
    "CREATE INDEX IF NOT EXISTS idx_resources_task  ON resources(task_id);",
    "CREATE INDEX IF NOT EXISTS idx_workflows_project ON workflows(project_id);",
]

SQL_MIGRATE_V1_TO_V2 = [
    "ALTER TABLE operations ADD COLUMN tool_name TEXT;",
    "ALTER TABLE operations ADD COLUMN skill_name TEXT;",
    "ALTER TABLE operations ADD COLUMN mcp_name TEXT;",
    "ALTER TABLE operations ADD COLUMN retry_count INTEGER DEFAULT 0;",
    "ALTER TABLE operations ADD COLUMN input_tokens INTEGER;",
    "ALTER TABLE operations ADD COLUMN output_tokens INTEGER;",
    "ALTER TABLE operations ADD COLUMN duration_seconds INTEGER;",
]

SQL_MIGRATE_V2_TO_V3 = [
    (
        "CREATE TABLE IF NOT EXISTS workflows "
        "(id TEXT PRIMARY KEY, project_id TEXT NOT NULL, title TEXT NOT NULL, "
        "source_file TEXT, status TEXT NOT NULL DEFAULT 'active' "
        "CHECK(status IN ('active','completed','archived')), "
        "created_at TEXT NOT NULL DEFAULT (datetime('now')));"
    ),
    "ALTER TABLE tasks ADD COLUMN workflow_id TEXT;",
    "ALTER TABLE operations ADD COLUMN workflow_id TEXT;",
    "CREATE INDEX IF NOT EXISTS idx_workflows_project ON workflows(project_id);",
]


def migrate_schema(conn):
    """Apply pending schema migrations. Idempotent.
    미완료 스키마 마이그레이션 적용. 멱등성 보장.
    """
    from datetime import datetime
    row = conn.execute(
        "SELECT value FROM settings WHERE key='__schema_version'"
    ).fetchone()
    current_version = int(row['value']) if row else 0

    if current_version < 2:
        existing_cols = {
            r[1] for r in conn.execute("PRAGMA table_info(operations)").fetchall()
        }
        if 'tool_name' not in existing_cols:
            for stmt in SQL_MIGRATE_V1_TO_V2:
                conn.execute(stmt)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, description, updated_at) "
            "VALUES ('__schema_version', '2', 'DB schema version', ?)",
            (now,)
        )
        conn.commit()

    if current_version < 3:
        existing_tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        tasks_cols = {r[1] for r in conn.execute(
            "PRAGMA table_info(tasks)"
        ).fetchall()}
        ops_cols = {r[1] for r in conn.execute(
            "PRAGMA table_info(operations)"
        ).fetchall()}
        for stmt in SQL_MIGRATE_V2_TO_V3:
            if 'ALTER TABLE tasks ADD COLUMN workflow_id' in stmt and 'workflow_id' in tasks_cols:
                continue
            if 'ALTER TABLE operations ADD COLUMN workflow_id' in stmt and 'workflow_id' in ops_cols:
                continue
            if 'CREATE TABLE IF NOT EXISTS workflows' in stmt and 'workflows' in existing_tables:
                continue
            try:
                conn.execute(stmt)
            except Exception:
                pass
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, description, updated_at) "
            "VALUES ('__schema_version', '3', 'DB schema version', ?)",
            (now,)
        )
        conn.commit()


def create_tables(conn):
    """Create all tables and indexes. Idempotent.
    모든 테이블과 인덱스를 생성. 멱등성 보장.
    """
    conn.execute(SQL_CREATE_TASKS)
    conn.execute(SQL_CREATE_WORKFLOWS)
    conn.execute(SQL_CREATE_OPERATIONS)
    conn.execute(SQL_CREATE_RESOURCES)
    conn.execute(SQL_CREATE_SETTINGS)
    conn.execute(SQL_CREATE_CHECKPOINTS)
    for idx_sql in SQL_CREATE_INDEXES:
        conn.execute(idx_sql)
    conn.commit()
