"""SQLite schema definition for TaskOps.
TaskOps DB 스키마 정의 모듈.
"""

SCHEMA_VERSION = 6

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
    workflow_id TEXT,                      -- NOT NULL for ETS types (v4+); only 'project' type may be NULL
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (type = 'project' OR workflow_id IS NOT NULL)
);
"""

SQL_CREATE_WORKFLOWS = """
CREATE TABLE IF NOT EXISTS workflows (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL,
    title       TEXT NOT NULL,
    description TEXT,
    source_file TEXT,
    status      TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active','completed','archived')),
    report      TEXT,
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
    workflow_id TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
"""

SQL_CREATE_SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL DEFAULT '',
    key         TEXT NOT NULL,
    value       TEXT NOT NULL,
    description TEXT,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(workflow_id, key)
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

# v4→v5: (1) Rebuild settings with workflow_id + composite unique key.
#         (2) Add report column to workflows.
SQL_MIGRATE_V4_TO_V5_SETTINGS_CREATE = (
    "CREATE TABLE settings_v5 ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "workflow_id TEXT NOT NULL DEFAULT '', "
    "key TEXT NOT NULL, "
    "value TEXT NOT NULL, "
    "description TEXT, "
    "updated_at TEXT NOT NULL DEFAULT (datetime('now')), "
    "UNIQUE(workflow_id, key)"
    ");"
)

# v3→v4: Add CHECK constraint (type='project' OR workflow_id IS NOT NULL)
# SQLite requires table recreation to add constraints.
# ETS records (epic/task/objective) without workflow_id are dropped with a warning.
SQL_MIGRATE_V3_TO_V4_CREATE = (
    "CREATE TABLE tasks_v4 ("
    "id TEXT PRIMARY KEY, "
    "project_id TEXT NOT NULL, "
    "type TEXT NOT NULL CHECK(type IN ('project','epic','task','objective')), "
    "title TEXT NOT NULL, "
    "description TEXT, "
    "status TEXT NOT NULL DEFAULT 'todo' "
    "CHECK(status IN ('todo','in_progress','interrupted','done','cancelled')), "
    "parent_id TEXT, "
    "todo TEXT, "
    "interrupt TEXT, "
    "milestone_target TEXT, "
    "due_date TEXT, "
    "seq_order INTEGER, "
    "parallel_group TEXT, "
    "depends_on TEXT, "
    "workflow_id TEXT, "
    "created_at TEXT NOT NULL DEFAULT (datetime('now')), "
    "updated_at TEXT NOT NULL DEFAULT (datetime('now')), "
    "CHECK (type = 'project' OR workflow_id IS NOT NULL)"
    ");"
)


SQL_MIGRATE_V5_TO_V6 = [
    "ALTER TABLE workflows ADD COLUMN description TEXT;",
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

    if current_version < 4:
        # Add workflow_id to resources table if not present
        res_cols = {r[1] for r in conn.execute("PRAGMA table_info(resources)").fetchall()}
        if 'workflow_id' not in res_cols:
            try:
                conn.execute("ALTER TABLE resources ADD COLUMN workflow_id TEXT;")
            except Exception:
                pass

        # Find ETS records without workflow_id (will be dropped)
        orphans = conn.execute(
            "SELECT id, type, title FROM tasks WHERE type != 'project' AND workflow_id IS NULL"
        ).fetchall()
        if orphans:
            print(f"[TaskOps migration v4] Warning: {len(orphans)} ETS record(s) have no workflow_id "
                  "and will be removed (workflow_id is now required for all ETS):")
            for r in orphans:
                print(f"  - {r['id']} ({r['type']}): {r['title']}")

        # Recreate tasks table with CHECK constraint
        conn.execute(SQL_MIGRATE_V3_TO_V4_CREATE)
        conn.execute(
            "INSERT INTO tasks_v4 SELECT * FROM tasks "
            "WHERE type = 'project' OR workflow_id IS NOT NULL"
        )
        conn.execute("DROP TABLE tasks")
        conn.execute("ALTER TABLE tasks_v4 RENAME TO tasks")

        # Recreate indexes
        for stmt in [
            "CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_tasks_parent  ON tasks(parent_id);",
            "CREATE INDEX IF NOT EXISTS idx_tasks_type    ON tasks(type);",
            "CREATE INDEX IF NOT EXISTS idx_tasks_status  ON tasks(status);",
        ]:
            conn.execute(stmt)

        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, description, updated_at) "
            "VALUES ('__schema_version', '4', 'DB schema version', ?)",
            (now,)
        )
        conn.commit()

    if current_version < 5:
        # Rebuild settings table: add workflow_id + composite unique (workflow_id, key)
        conn.execute(SQL_MIGRATE_V4_TO_V5_SETTINGS_CREATE)
        conn.execute(
            "INSERT INTO settings_v5 (workflow_id, key, value, description, updated_at) "
            "SELECT '', key, value, description, updated_at FROM settings"
        )
        conn.execute("DROP TABLE settings")
        conn.execute("ALTER TABLE settings_v5 RENAME TO settings")

        # Add report column to workflows if not present
        wf_cols = {r[1] for r in conn.execute("PRAGMA table_info(workflows)").fetchall()}
        if 'report' not in wf_cols:
            conn.execute("ALTER TABLE workflows ADD COLUMN report TEXT;")

        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO settings (workflow_id, key, value, description, updated_at) "
            "VALUES ('', '__schema_version', '5', 'DB schema version', ?) "
            "ON CONFLICT(workflow_id, key) DO UPDATE SET value='5', updated_at=?",
            (now, now)
        )
        conn.commit()

    if current_version < 6:
        wf_cols = {r[1] for r in conn.execute("PRAGMA table_info(workflows)").fetchall()}
        if 'description' not in wf_cols:
            for stmt in SQL_MIGRATE_V5_TO_V6:
                conn.execute(stmt)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO settings (workflow_id, key, value, description, updated_at) "
            "VALUES ('', '__schema_version', '6', 'DB schema version', ?) "
            "ON CONFLICT(workflow_id, key) DO UPDATE SET value='6', updated_at=?",
            (now, now)
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
