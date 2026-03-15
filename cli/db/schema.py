"""SQLite schema definition for TaskOps.
TaskOps DB 스키마 정의 모듈.
"""

SCHEMA_VERSION = 1

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
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

SQL_CREATE_OPERATIONS = """
CREATE TABLE IF NOT EXISTS operations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT NOT NULL,
    operation_type  TEXT NOT NULL
                    CHECK(operation_type IN ('start','progress','complete','error','interrupt')),
    agent_platform  TEXT,
    summary         TEXT,
    details         TEXT,
    subagent_used   INTEGER DEFAULT 0,
    subagent_result TEXT,
    started_at      TEXT,
    completed_at    TEXT,
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
]


def create_tables(conn):
    """Create all tables and indexes. Idempotent.
    모든 테이블과 인덱스를 생성. 멱등성 보장.
    """
    conn.execute(SQL_CREATE_TASKS)
    conn.execute(SQL_CREATE_OPERATIONS)
    conn.execute(SQL_CREATE_RESOURCES)
    conn.execute(SQL_CREATE_SETTINGS)
    conn.execute(SQL_CREATE_CHECKPOINTS)
    for idx_sql in SQL_CREATE_INDEXES:
        conn.execute(idx_sql)
    conn.commit()
