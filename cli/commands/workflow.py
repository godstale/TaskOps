"""Workflow management command.
Workflow 관리 커맨드. 순차/병렬 실행 순서 및 의존성 관리.
"""
import json
from .utils import get_db
from ..db.connection import close_connection


def register(subparsers):
    parser = subparsers.add_parser('workflow', help='Manage workflow')
    sub = parser.add_subparsers(dest='subcommand')

    set_order = sub.add_parser('set-order', help='Set task execution order')
    set_order.add_argument('task_ids', nargs='+', help='Task IDs in order')
    set_order.set_defaults(func=handle_set_order)

    set_parallel = sub.add_parser('set-parallel', help='Set parallel execution group')
    set_parallel.add_argument('--group', required=True, help='Group name')
    set_parallel.add_argument('task_ids', nargs='+', help='Task IDs')
    set_parallel.set_defaults(func=handle_set_parallel)

    add_dep = sub.add_parser('add-dep', help='Add dependency')
    add_dep.add_argument('task_id', help='Task ID')
    add_dep.add_argument('--depends-on', nargs='+', required=True, help='Dependency task IDs')
    add_dep.set_defaults(func=handle_add_dep)

    show = sub.add_parser('show', help='Show workflow')
    show.add_argument('--workflow', default=None, help='Filter by workflow ID')
    show.set_defaults(func=handle_show)

    nxt = sub.add_parser('next', help='Show next executable tasks')
    nxt.add_argument('--workflow', default=None, help='Filter by workflow ID')
    nxt.set_defaults(func=handle_next)

    current = sub.add_parser('current', help='Show currently active task')
    current.add_argument('--workflow', default=None, help='Filter by workflow ID')
    current.set_defaults(func=handle_current)

    create = sub.add_parser('create', help='Create a new workflow')
    create.add_argument('--title', required=True, help='Workflow title')
    create.add_argument('--source-file', dest='source_file', help='Original TODO file path (optional)')
    create.set_defaults(func=handle_create)

    wf_list = sub.add_parser('list', help='List all workflows')
    wf_list.set_defaults(func=handle_list)

    delete = sub.add_parser('delete', help='Delete a workflow and all its tasks')
    delete.add_argument('workflow_id', help='Workflow ID to delete (e.g. PRJ-W001)')
    delete.set_defaults(func=handle_delete)

    imp = sub.add_parser('import', help='Import TODO structure into workflow as ETS')
    imp.add_argument('workflow_id', help='Target workflow ID (e.g. PRJ-W001)')
    imp_group = imp.add_mutually_exclusive_group(required=True)
    imp_group.add_argument('--structure', help='JSON structure string')
    imp_group.add_argument('--structure-file', dest='structure_file',
                           help='Path to JSON structure file')
    imp.set_defaults(func=handle_import)

    restart = sub.add_parser('restart', help='Reset workflow tasks to todo for re-execution')
    restart.add_argument('workflow_id', help='Workflow ID to restart (e.g. PRJ-W001)')
    restart.add_argument('--clear-ops', action='store_true',
                         help='Also clear operation records for this workflow')
    restart.set_defaults(func=handle_restart)

    exp = sub.add_parser('export', help='Export workflow to TODO.md format')
    exp.add_argument('workflow_id', help='Workflow ID (e.g. TST-W001)')
    exp.add_argument('--output', default=None,
                     help='Output file path (default: TODO.md next to taskops.db)')
    exp.set_defaults(func=handle_export)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle_set_order(args):
    conn = get_db(args)
    try:
        for i, task_id in enumerate(args.task_ids, start=1):
            row = conn.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row is None:
                print(f"Task not found: {task_id}")
                raise SystemExit(1)
            conn.execute("UPDATE tasks SET seq_order=? WHERE id=?", (i, task_id))
        conn.commit()
        print(f"Set execution order for {len(args.task_ids)} tasks:")
        for i, tid in enumerate(args.task_ids, start=1):
            print(f"  {i}. {tid}")
    finally:
        close_connection(conn)


def handle_set_parallel(args):
    conn = get_db(args)
    try:
        for task_id in args.task_ids:
            row = conn.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row is None:
                print(f"Task not found: {task_id}")
                raise SystemExit(1)
            conn.execute(
                "UPDATE tasks SET parallel_group=? WHERE id=?",
                (args.group, task_id)
            )
        conn.commit()
        print(f"Set parallel group '{args.group}' for: {', '.join(args.task_ids)}")
    finally:
        close_connection(conn)


def handle_add_dep(args):
    conn = get_db(args)
    try:
        row = conn.execute(
            "SELECT id, depends_on FROM tasks WHERE id=?", (args.task_id,)
        ).fetchone()
        if row is None:
            print(f"Task not found: {args.task_id}")
            raise SystemExit(1)

        # Validate dependency targets exist
        for dep_id in args.depends_on:
            dep = conn.execute("SELECT id FROM tasks WHERE id=?", (dep_id,)).fetchone()
            if dep is None:
                print(f"Dependency task not found: {dep_id}")
                raise SystemExit(1)

        # Merge with existing depends_on
        existing = json.loads(row['depends_on']) if row['depends_on'] else []
        for dep_id in args.depends_on:
            if dep_id not in existing:
                existing.append(dep_id)

        conn.execute(
            "UPDATE tasks SET depends_on=? WHERE id=?",
            (json.dumps(existing), args.task_id)
        )
        conn.commit()
        print(f"Task {args.task_id} now depends on: {', '.join(existing)}")
    finally:
        close_connection(conn)


def handle_show(args):
    conn = get_db(args)
    try:
        query = ("SELECT id, title, status, seq_order, parallel_group, depends_on "
                 "FROM tasks WHERE type='task' AND seq_order IS NOT NULL")
        params = []
        workflow_filter = getattr(args, 'workflow', None)
        if workflow_filter:
            query += " AND workflow_id=?"
            params.append(workflow_filter)
        query += " ORDER BY seq_order, id"
        rows = conn.execute(query, params).fetchall()

        if not rows:
            print("No workflow defined. Use 'workflow set-order' to define execution order.")
            return

        print("Workflow:")
        current_order = None
        for row in rows:
            order = row['seq_order']
            check = 'x' if row['status'] == 'done' else ' '
            group = f" [group: {row['parallel_group']}]" if row['parallel_group'] else ""
            deps = ""
            if row['depends_on']:
                dep_list = json.loads(row['depends_on'])
                deps = f" (depends: {', '.join(dep_list)})"

            if order != current_order:
                current_order = order
                print(f"  {order}. [{check}] {row['id']}: {row['title']} ({row['status']}){group}{deps}")
            else:
                print(f"     [{check}] {row['id']}: {row['title']} ({row['status']}){group}{deps}")
    finally:
        close_connection(conn)


def _deps_satisfied(conn, depends_on_json):
    """Check if all dependencies are done. Python-based for compatibility."""
    if not depends_on_json:
        return True
    dep_ids = json.loads(depends_on_json)
    if not dep_ids:
        return True
    placeholders = ','.join('?' for _ in dep_ids)
    row = conn.execute(
        f"SELECT COUNT(*) as cnt FROM tasks WHERE id IN ({placeholders}) AND status != 'done'",
        dep_ids
    ).fetchone()
    return row['cnt'] == 0


def handle_next(args):
    conn = get_db(args)
    try:
        query = ("SELECT id, title, seq_order, parallel_group, depends_on FROM tasks "
                 "WHERE status = 'todo' AND type = 'task'")
        params = []
        workflow_filter = getattr(args, 'workflow', None)
        if workflow_filter:
            query += " AND workflow_id=?"
            params.append(workflow_filter)
        query += " ORDER BY seq_order ASC, id ASC"
        rows = conn.execute(query, params).fetchall()

        executable = []
        for row in rows:
            if _deps_satisfied(conn, row['depends_on']):
                executable.append(row)

        if not executable:
            print("No executable tasks. All tasks may be done or blocked.")
            return

        print("Next executable tasks:")
        for row in executable:
            group = f" [group: {row['parallel_group']}]" if row['parallel_group'] else ""
            print(f"  {row['id']}: {row['title']}{group}")
    finally:
        close_connection(conn)


def handle_current(args):
    conn = get_db(args)
    try:
        query = "SELECT id FROM tasks WHERE status='in_progress' AND type='task'"
        params = []
        workflow_filter = getattr(args, 'workflow', None)
        if workflow_filter:
            query += " AND workflow_id=?"
            params.append(workflow_filter)
        query += " ORDER BY seq_order, id LIMIT 1"
        row = conn.execute(query, params).fetchone()
        if row is None:
            # No output for scripting use (hooks)
            return
        print(row['id'])
    finally:
        close_connection(conn)


def handle_create(args):
    from .utils import get_project_id, next_workflow_id
    from datetime import datetime
    conn = get_db(args)
    try:
        project_id = get_project_id(conn)
        wf_id = next_workflow_id(conn, project_id)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        conn.execute(
            "INSERT INTO workflows (id, project_id, title, source_file, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (wf_id, project_id, args.title, getattr(args, 'source_file', None), now)
        )
        conn.commit()
        print(f"Created workflow {wf_id}: {args.title}")
    finally:
        close_connection(conn)


def handle_list(args):
    conn = get_db(args)
    try:
        rows = conn.execute(
            "SELECT id, title, status, source_file FROM workflows ORDER BY id"
        ).fetchall()
        if not rows:
            print("No workflows found.")
            return
        for row in rows:
            src = f" (from: {row['source_file']})" if row['source_file'] else ""
            print(f"  {row['id']}: {row['title']} [{row['status']}]{src}")
    finally:
        close_connection(conn)


def handle_delete(args):
    conn = get_db(args)
    try:
        wf = conn.execute(
            "SELECT id FROM workflows WHERE id=?", (args.workflow_id,)
        ).fetchone()
        if not wf:
            print(f"Workflow not found: {args.workflow_id}")
            raise SystemExit(1)
        # Cascade: delete operations and resources for tasks in this workflow, then tasks, then workflow
        tasks = conn.execute(
            "SELECT id FROM tasks WHERE workflow_id=?", (args.workflow_id,)
        ).fetchall()
        for task in tasks:
            conn.execute("DELETE FROM operations WHERE task_id=?", (task['id'],))
            conn.execute("DELETE FROM resources WHERE task_id=?", (task['id'],))
        conn.execute("DELETE FROM tasks WHERE workflow_id=?", (args.workflow_id,))
        conn.execute("DELETE FROM workflows WHERE id=?", (args.workflow_id,))
        conn.commit()
        print(f"Deleted workflow {args.workflow_id} and its tasks.")
    finally:
        close_connection(conn)


def handle_import(args):
    import json as _json
    from datetime import datetime
    from .utils import get_project_id, next_id

    # Parse JSON input
    if args.structure:
        try:
            structure = _json.loads(args.structure)
        except _json.JSONDecodeError as e:
            print(f"Error: Invalid JSON: {e}")
            raise SystemExit(1)
    else:
        try:
            with open(args.structure_file, encoding='utf-8') as f:
                structure = _json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found: {args.structure_file}")
            raise SystemExit(1)
        except _json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in file: {e}")
            raise SystemExit(1)

    conn = get_db(args)
    try:
        # Validate workflow exists
        wf = conn.execute(
            "SELECT id, title FROM workflows WHERE id=?", (args.workflow_id,)
        ).fetchone()
        if not wf:
            print(f"Error: Workflow not found: {args.workflow_id}")
            raise SystemExit(1)

        project_id = get_project_id(conn)
        now = datetime.now().isoformat(sep=' ', timespec='seconds')

        # Replace: delete all existing tasks in this workflow
        existing = conn.execute(
            "SELECT id FROM tasks WHERE workflow_id=?", (args.workflow_id,)
        ).fetchall()
        for task in existing:
            conn.execute("DELETE FROM operations WHERE task_id=?", (task['id'],))
            conn.execute("DELETE FROM resources WHERE task_id=?", (task['id'],))
        conn.execute("DELETE FROM tasks WHERE workflow_id=?", (args.workflow_id,))

        output_lines = [f"Workflow {wf['id']}: {wf['title']}"]
        seq = 1

        for epic_data in structure.get('epics', []):
            epic_id = next_id(conn, project_id, 'E')
            conn.execute(
                "INSERT INTO tasks "
                "(id, project_id, type, title, description, status, "
                "parent_id, workflow_id, created_at, updated_at) "
                "VALUES (?, ?, 'epic', ?, ?, 'todo', ?, ?, ?, ?)",
                (epic_id, project_id,
                 epic_data['title'], epic_data.get('description', ''),
                 project_id, args.workflow_id, now, now)
            )
            output_lines.append(f"  Epic {epic_id}: {epic_data['title']}")

            for task_data in epic_data.get('tasks', []):
                task_id = next_id(conn, project_id, 'T')
                conn.execute(
                    "INSERT INTO tasks "
                    "(id, project_id, type, title, description, status, "
                    "parent_id, workflow_id, seq_order, created_at, updated_at) "
                    "VALUES (?, ?, 'task', ?, ?, 'todo', ?, ?, ?, ?, ?)",
                    (task_id, project_id,
                     task_data['title'], task_data.get('description', ''),
                     epic_id, args.workflow_id, seq, now, now)
                )
                output_lines.append(f"    {task_id}: {task_data['title']}")
                seq += 1

                for res_data in task_data.get('resources', []):
                    conn.execute(
                        "INSERT INTO resources (task_id, file_path, description, res_type, created_at) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (task_id, res_data['path'], res_data.get('desc', ''),
                         res_data.get('type', 'reference'), now)
                    )
                    output_lines.append(f"      [resource] {res_data['path']} ({res_data.get('type', 'reference')})")

                for st_data in task_data.get('tasks', task_data.get('subtasks', [])):
                    st_id = next_id(conn, project_id, 'T')
                    conn.execute(
                        "INSERT INTO tasks "
                        "(id, project_id, type, title, description, status, "
                        "parent_id, workflow_id, seq_order, created_at, updated_at) "
                        "VALUES (?, ?, 'task', ?, ?, 'todo', ?, ?, ?, ?, ?)",
                        (st_id, project_id,
                         st_data['title'], st_data.get('description', ''),
                         task_id, args.workflow_id, seq, now, now)
                    )
                    output_lines.append(f"      {st_id}: {st_data['title']}")
                    seq += 1

                    for res_data in st_data.get('resources', []):
                        conn.execute(
                            "INSERT INTO resources (task_id, file_path, description, res_type, created_at) "
                            "VALUES (?, ?, ?, ?, ?)",
                            (st_id, res_data['path'], res_data.get('desc', ''),
                             res_data.get('type', 'reference'), now)
                        )
                        output_lines.append(f"        [resource] {res_data['path']} ({res_data.get('type', 'reference')})")

        conn.commit()
        print('\n'.join(output_lines))
    finally:
        close_connection(conn)


def handle_restart(args):
    from datetime import datetime
    from .utils import get_project_id

    conn = get_db(args)
    try:
        # Validate workflow exists
        wf = conn.execute(
            "SELECT id, title FROM workflows WHERE id=?", (args.workflow_id,)
        ).fetchone()
        if not wf:
            print(f"Workflow not found: {args.workflow_id}")
            raise SystemExit(1)

        # Auto-save checkpoint before restart
        project_id = get_project_id(conn)
        rows = conn.execute(
            "SELECT id, status, interrupt FROM tasks "
            "WHERE project_id=? AND type != 'project'",
            (project_id,)
        ).fetchall()
        snapshot = {r['id']: {'status': r['status'], 'interrupt': r['interrupt']} for r in rows}
        conn.execute(
            "INSERT INTO checkpoints (note, snapshot) VALUES (?, ?)",
            (f"[auto] before workflow restart {args.workflow_id}", json.dumps(snapshot))
        )

        # Reset only tasks belonging to this workflow
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        result = conn.execute(
            "UPDATE tasks SET status='todo', interrupt=NULL, updated_at=? "
            "WHERE workflow_id=? AND type != 'project'",
            (now, args.workflow_id)
        )
        reset_count = result.rowcount

        if args.clear_ops:
            task_ids = conn.execute(
                "SELECT id FROM tasks WHERE workflow_id=?", (args.workflow_id,)
            ).fetchall()
            for t in task_ids:
                conn.execute("DELETE FROM operations WHERE task_id=?", (t['id'],))
            print(f"  Operation history cleared for {args.workflow_id}.")

        conn.commit()
        print(f"Workflow {args.workflow_id} restarted: {reset_count} tasks reset to 'todo'")
        print("  Auto-checkpoint saved before restart.")
    finally:
        close_connection(conn)


def handle_export(args):
    import os
    from datetime import datetime
    from .utils import get_project_dir

    conn = get_db(args)
    try:
        wf = conn.execute(
            "SELECT id, title FROM workflows WHERE id=?", (args.workflow_id,)
        ).fetchone()
        if not wf:
            print(f"Error: Workflow not found: {args.workflow_id}")
            raise SystemExit(1)

        out_path = os.path.abspath(args.output) if args.output else \
            os.path.join(get_project_dir(args), 'TODO.md')

        project = conn.execute(
            "SELECT title FROM tasks WHERE type='project' LIMIT 1"
        ).fetchone()
        project_name = project['title'] if project else 'Project'

        epics = conn.execute(
            "SELECT id, title, status FROM tasks "
            "WHERE type='epic' AND workflow_id=? ORDER BY id",
            (args.workflow_id,)
        ).fetchall()

        lines = [
            f"# {project_name}",
            f"> Workflow: {wf['title']} ({wf['id']}) | "
            f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
        ]

        def append_tasks(parent_id, indent):
            rows = conn.execute(
                "SELECT id, title, status FROM tasks "
                "WHERE type='task' AND parent_id=? ORDER BY seq_order, id",
                (parent_id,)
            ).fetchall()
            for t in rows:
                marker = 'x' if t['status'] == 'done' else ' '
                lines.append(f"{'  ' * indent}- [{marker}] {t['title']} `{t['id']}`")
                append_tasks(t['id'], indent + 1)

        for epic in epics:
            lines.append(f"### {epic['title']} `{epic['id']}`")
            append_tasks(epic['id'], 0)
            lines.append("")

        lines.append("---")
        lines.append("*Generated by TaskOps*")

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"Exported {args.workflow_id} to {out_path}")
    finally:
        close_connection(conn)
