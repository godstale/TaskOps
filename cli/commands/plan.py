"""Plan management command.
Plan 관리 커맨드. 프로젝트 계획 변경사항을 DB에 적용.
"""
import json
from datetime import datetime
from .utils import get_db, get_project_id, get_project_dir, next_id, get_workflow_prefix
from ..db.connection import close_connection


def register(subparsers, parents=None):
    parser = subparsers.add_parser('plan', help='Manage project plan', parents=parents or [])
    sub = parser.add_subparsers(dest='subcommand')

    update = sub.add_parser('update', help='Apply plan changes to DB')
    group = update.add_mutually_exclusive_group(required=True)
    group.add_argument('--changes', help='JSON string of changes')
    group.add_argument('--changes-file', help='Path to JSON file of changes')
    update.add_argument('--workflow', help='Workflow ID for new creates (required if "create" items are present)')
    update.set_defaults(func=handle_update)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle_update(args):
    # Parse JSON input
    if args.changes:
        try:
            changes = json.loads(args.changes)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON: {e}")
            raise SystemExit(1)
    else:
        try:
            with open(args.changes_file, encoding='utf-8') as f:
                changes = json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found: {args.changes_file}")
            raise SystemExit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in file: {e}")
            raise SystemExit(1)

    creates = changes.get('create', [])
    updates = changes.get('update', [])
    deletes = changes.get('delete', [])

    # Validate: creates require a workflow_id (via --workflow flag or per-item workflow_id)
    workflow_arg = getattr(args, 'workflow', None)
    if creates and not workflow_arg:
        missing = [i for i in creates if not i.get('workflow_id')]
        if missing:
            print("Error: 'create' items require a workflow_id. "
                  "Pass --workflow <W-ID> or include 'workflow_id' in each create item.")
            raise SystemExit(1)

    conn = get_db(args)
    try:
        project_id = get_project_id(conn)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')

        # --- Validate all items before touching DB ---
        valid_creates = _validate_creates(conn, creates)
        valid_updates = _validate_updates(conn, updates)
        valid_deletes = _validate_deletes(conn, deletes)

        # --- Apply in single transaction ---
        created_ids = []
        updated_ids = []
        deleted_ids = []

        try:
            for item in valid_creates:
                type_char = 'E' if item['type'] == 'epic' else 'T'
                effective_wf_id = item.get('workflow_id') or workflow_arg
                wf_short = get_workflow_prefix(effective_wf_id)
                new_id = next_id(conn, wf_short, type_char)
                conn.execute(
                    "INSERT INTO tasks "
                    "(id, project_id, type, title, description, status, parent_id, workflow_id, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (new_id, project_id, item['type'], item['title'],
                     item.get('description', ''), item.get('status', 'todo'),
                     item.get('parent_id'),
                     item.get('workflow_id') or workflow_arg,
                     now, now)
                )
                created_ids.append(new_id)

            for item in valid_updates:
                fields, params = [], []
                for field in ('title', 'description', 'status'):
                    if field in item:
                        fields.append(f"{field}=?")
                        params.append(item[field])
                if fields:
                    fields.append("updated_at=?")
                    params.append(now)
                    params.append(item['id'])
                    conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id=?", params)
                    updated_ids.append(item['id'])

            for task_id in valid_deletes:
                _cascade_delete(conn, task_id)
                deleted_ids.append(task_id)

            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error applying changes (rolled back): {e}")
            raise SystemExit(1)

        # --- Report results ---
        if created_ids:
            print(f"Created: {', '.join(created_ids)}")
        if updated_ids:
            print(f"Updated: {', '.join(updated_ids)}")
        if deleted_ids:
            print(f"Deleted: {', '.join(deleted_ids)}")
        if not (created_ids or updated_ids or deleted_ids):
            print("No changes applied.")
            return

    finally:
        close_connection(conn)


def _validate_creates(conn, creates):
    valid = []
    for item in creates:
        if not item.get('title'):
            print(f"Warning: create item missing title, skipping: {item}")
            continue
        item_type = item.get('type')
        if item_type not in ('epic', 'task'):
            print(f"Warning: create item has invalid type '{item_type}', skipping")
            continue
        if item_type == 'task':
            parent_id = item.get('parent_id')
            if not parent_id:
                print(f"Warning: task '{item['title']}' missing parent_id, skipping")
                continue
            parent = conn.execute(
                "SELECT type FROM tasks WHERE id=?", (parent_id,)
            ).fetchone()
            if not parent:
                print(f"Warning: parent_id '{parent_id}' not found for task '{item['title']}', skipping")
                continue
            if parent['type'] not in ('epic', 'task'):
                print(f"Warning: parent '{parent_id}' is not an epic or task, skipping")
                continue
        valid.append(item)
    return valid


def _validate_updates(conn, updates):
    valid = []
    for item in updates:
        task_id = item.get('id')
        if not task_id:
            print(f"Warning: update item missing id, skipping: {item}")
            continue
        if not conn.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone():
            print(f"Warning: task '{task_id}' not found for update, skipping")
            continue
        valid.append(item)
    return valid


def _validate_deletes(conn, deletes):
    valid = []
    for item in deletes:
        task_id = item.get('id')
        if not task_id:
            print(f"Warning: delete item missing id, skipping: {item}")
            continue
        if not conn.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone():
            print(f"Warning: task '{task_id}' not found for delete, skipping")
            continue
        valid.append(task_id)
    return valid


def _cascade_delete(conn, task_id):
    """Delete task and all descendants recursively, including their operations and resources."""
    children = conn.execute(
        "SELECT id FROM tasks WHERE parent_id=?", (task_id,)
    ).fetchall()
    for child in children:
        _cascade_delete(conn, child['id'])
    conn.execute("DELETE FROM operations WHERE task_id=?", (task_id,))
    conn.execute("DELETE FROM resources WHERE task_id=?", (task_id,))
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
