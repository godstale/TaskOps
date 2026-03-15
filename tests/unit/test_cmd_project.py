"""Tests for cli/commands/project.py — checkpoint, rollback, restart commands.
project 커맨드 테스트: 체크포인트, 롤백, 재시작.
"""
import json
import argparse
import pytest
from cli.db.connection import get_connection, close_connection
from cli.commands.project import (
    _snapshot_tasks,
    _create_checkpoint,
    _list_checkpoints,
    handle_rollback,
    handle_restart,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def make_args(db_path, **kwargs):
    """Build a Namespace that get_db() can use."""
    return argparse.Namespace(db=db_path, **kwargs)


def seed_project(conn):
    """Insert a minimal project + epic + 2 tasks into conn."""
    conn.execute(
        "INSERT INTO tasks (id, project_id, type, title, status) VALUES (?,?,?,?,?)",
        ("TST", "TST", "project", "Test Project", "in_progress")
    )
    conn.execute(
        "INSERT INTO tasks (id, project_id, type, title, status, parent_id) VALUES (?,?,?,?,?,?)",
        ("TST-E001", "TST", "epic", "Epic 1", "todo", "TST")
    )
    conn.execute(
        "INSERT INTO tasks (id, project_id, type, title, status, parent_id) VALUES (?,?,?,?,?,?)",
        ("TST-T001", "TST", "task", "Task 1", "todo", "TST-E001")
    )
    conn.execute(
        "INSERT INTO tasks (id, project_id, type, title, status, parent_id) VALUES (?,?,?,?,?,?)",
        ("TST-T002", "TST", "task", "Task 2", "done", "TST-E001")
    )
    conn.commit()


# ── _snapshot_tasks ───────────────────────────────────────────────────────────

def test_snapshot_excludes_project_row(tmp_db):
    conn, _ = tmp_db
    seed_project(conn)
    snap = _snapshot_tasks(conn, "TST")
    assert "TST" not in snap           # project root excluded
    assert "TST-E001" in snap          # epic included
    assert "TST-T001" in snap
    assert "TST-T002" in snap


def test_snapshot_captures_status(tmp_db):
    conn, _ = tmp_db
    seed_project(conn)
    snap = _snapshot_tasks(conn, "TST")
    assert snap["TST-T001"]["status"] == "todo"
    assert snap["TST-T002"]["status"] == "done"


# ── _create_checkpoint ────────────────────────────────────────────────────────

def test_create_checkpoint_inserts_row(tmp_db, capsys):
    conn, db_path = tmp_db
    seed_project(conn)
    # conn stays open; _create_checkpoint opens its own connection
    args = make_args(db_path, note="test checkpoint")
    _create_checkpoint(args)

    rows = conn.execute("SELECT * FROM checkpoints").fetchall()
    assert len(rows) == 1
    assert rows[0]["note"] == "test checkpoint"


def test_create_checkpoint_snapshot_is_valid_json(tmp_db):
    conn, db_path = tmp_db
    seed_project(conn)

    args = make_args(db_path, note="")
    _create_checkpoint(args)

    row = conn.execute("SELECT snapshot FROM checkpoints").fetchone()
    snap = json.loads(row["snapshot"])
    assert isinstance(snap, dict)
    assert "TST-T001" in snap


def test_create_checkpoint_prints_id(tmp_db, capsys):
    conn, db_path = tmp_db
    seed_project(conn)

    args = make_args(db_path, note="my note")
    _create_checkpoint(args)

    out = capsys.readouterr().out
    assert "Checkpoint #1" in out
    assert "my note" in out


# ── _list_checkpoints ─────────────────────────────────────────────────────────

def test_list_checkpoints_empty(tmp_db, capsys):
    conn, db_path = tmp_db
    seed_project(conn)

    args = make_args(db_path)
    _list_checkpoints(args)

    out = capsys.readouterr().out
    assert "No checkpoints found" in out


def test_list_checkpoints_shows_rows(tmp_db, capsys):
    conn, db_path = tmp_db
    seed_project(conn)

    # create two checkpoints
    _create_checkpoint(make_args(db_path, note="first"))
    _create_checkpoint(make_args(db_path, note="second"))

    _list_checkpoints(make_args(db_path))
    out = capsys.readouterr().out
    assert "first" in out
    assert "second" in out


# ── handle_rollback ───────────────────────────────────────────────────────────

def test_rollback_restores_status(tmp_db):
    conn, db_path = tmp_db
    seed_project(conn)

    # checkpoint when T002=done
    _create_checkpoint(make_args(db_path, note="snap1"))

    # change T002 to todo
    conn.execute("UPDATE tasks SET status='todo' WHERE id='TST-T002'")
    conn.commit()

    # rollback to checkpoint #1
    handle_rollback(make_args(db_path, checkpoint=1))

    row = conn.execute("SELECT status FROM tasks WHERE id='TST-T002'").fetchone()
    assert row["status"] == "done"


def test_rollback_creates_auto_checkpoint(tmp_db):
    conn, db_path = tmp_db
    seed_project(conn)

    _create_checkpoint(make_args(db_path, note="snap1"))
    handle_rollback(make_args(db_path, checkpoint=1))

    rows = conn.execute("SELECT note FROM checkpoints ORDER BY id").fetchall()
    assert len(rows) == 2
    assert "[auto]" in rows[1]["note"]


def test_rollback_missing_checkpoint_prints_error(tmp_db, capsys):
    conn, db_path = tmp_db
    seed_project(conn)

    handle_rollback(make_args(db_path, checkpoint=999))
    out = capsys.readouterr().out
    assert "not found" in out


def test_rollback_resets_post_checkpoint_tasks(tmp_db):
    conn, db_path = tmp_db
    seed_project(conn)

    # checkpoint with only T001, T002
    _create_checkpoint(make_args(db_path, note="before T003"))

    # add T003 after checkpoint
    conn.execute(
        "INSERT INTO tasks (id, project_id, type, title, status, parent_id) VALUES (?,?,?,?,?,?)",
        ("TST-T003", "TST", "task", "Task 3", "done", "TST-E001")
    )
    conn.commit()

    # rollback to snap before T003 existed
    handle_rollback(make_args(db_path, checkpoint=1))

    row = conn.execute("SELECT status FROM tasks WHERE id='TST-T003'").fetchone()
    assert row["status"] == "todo"   # reset to todo since not in snapshot


# ── handle_restart ────────────────────────────────────────────────────────────

def test_restart_resets_all_tasks(tmp_db):
    conn, db_path = tmp_db
    seed_project(conn)

    handle_restart(make_args(db_path, clear_ops=False))

    rows = conn.execute(
        "SELECT status FROM tasks WHERE project_id='TST' AND type!='project'"
    ).fetchall()
    assert all(r["status"] == "todo" for r in rows)


def test_restart_creates_auto_checkpoint(tmp_db):
    conn, db_path = tmp_db
    seed_project(conn)

    handle_restart(make_args(db_path, clear_ops=False))

    row = conn.execute("SELECT note FROM checkpoints").fetchone()
    assert row is not None
    assert "restart" in row["note"]


def test_restart_clear_ops_deletes_operations(tmp_db):
    conn, db_path = tmp_db
    seed_project(conn)
    conn.execute(
        "INSERT INTO operations (task_id, operation_type, agent_platform) VALUES (?,?,?)",
        ("TST-T001", "start", "test")
    )
    conn.commit()

    handle_restart(make_args(db_path, clear_ops=True))

    count = conn.execute("SELECT COUNT(*) FROM operations").fetchone()[0]
    assert count == 0


def test_restart_preserves_ops_by_default(tmp_db):
    conn, db_path = tmp_db
    seed_project(conn)
    conn.execute(
        "INSERT INTO operations (task_id, operation_type, agent_platform) VALUES (?,?,?)",
        ("TST-T001", "start", "test")
    )
    conn.commit()

    handle_restart(make_args(db_path, clear_ops=False))

    count = conn.execute("SELECT COUNT(*) FROM operations").fetchone()[0]
    assert count == 1
