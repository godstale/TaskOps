"""Agent activity monitoring command.
에이전트 활동 모니터링 커맨드.
"""
import json
import os
import sys
from datetime import datetime, timezone
from .utils import get_db
from ..db.connection import close_connection


def register(subparsers):
    parser = subparsers.add_parser('monitor', help='Monitor agent activity')
    sub = parser.add_subparsers(dest='subcommand')

    # record
    rec = sub.add_parser('record', help='Record a single agent event (called by hooks)')
    rec.add_argument('--event', required=True,
                     choices=['tool_use', 'tool_result', 'thinking', 'subagent_start', 'subagent_end'],
                     help='Event type')
    rec.add_argument('--tool', default=None, help='Tool name')
    rec.add_argument('--task', default=None, help='Active task ID')
    rec.add_argument('--source', default='hook', choices=['hook', 'jsonl'], help='Event source')
    rec.set_defaults(func=handle_record)

    # parse
    prs = sub.add_parser('parse', help='Parse JSONL session file and import events')
    prs.add_argument('--auto', action='store_true', help='Auto-detect latest JSONL file')
    prs.add_argument('--session', default=None, help='Specific session hash/ID')
    prs.add_argument('--workflow', default=None, help='Workflow ID to associate with events')
    prs.set_defaults(func=handle_parse)

    # report
    rep = sub.add_parser('report', help='Show tool usage report')
    rep.add_argument('--workflow', default=None, help='Filter by workflow ID')
    rep.set_defaults(func=handle_report)

    # summary
    summ = sub.add_parser('summary', help='Show session summary')
    summ.add_argument('--session', default=None, help='Session hash (defaults to most recent)')
    summ.set_defaults(func=handle_summary)

    parser.set_defaults(func=lambda args: parser.print_help())


# ---------------------------------------------------------------------------
# record
# ---------------------------------------------------------------------------

def handle_record(args):
    try:
        conn = get_db(args)
        session_id = os.environ.get('CLAUDE_SESSION_ID') or None

        workflow_id = None
        if args.task:
            row = conn.execute(
                "SELECT workflow_id FROM tasks WHERE id=?", (args.task,)
            ).fetchone()
            if row:
                workflow_id = row['workflow_id']

        now = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
        conn.execute(
            "INSERT OR IGNORE INTO agent_events "
            "(session_id, workflow_id, task_id, event_type, tool_name, "
            " event_timestamp, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, workflow_id, args.task, args.event, args.tool, now, args.source)
        )
        conn.commit()
    except Exception:
        pass
    finally:
        try:
            close_connection(conn)
        except Exception:
            pass
    sys.exit(0)


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------

def handle_parse(args):
    jsonl_path = _find_jsonl(args)
    if not jsonl_path:
        print("[monitor parse] No JSONL file found. Skipping.")
        return

    print(f"[monitor parse] Parsing: {jsonl_path}")

    try:
        conn = get_db(args)

        # Auto-detect workflow when --auto is used and --workflow is not specified
        workflow = getattr(args, 'workflow', None)
        if not workflow and getattr(args, 'auto', False):
            workflow = _detect_current_workflow(conn)
            if workflow:
                print(f"[monitor parse] Auto-detected workflow: {workflow}")

        events = _parse_jsonl(jsonl_path)
        inserted = _import_events(conn, events, workflow)
        conn.commit()
        print(f"[monitor parse] Imported {inserted} events from {len(events)} parsed.")
    except Exception as e:
        print(f"[monitor parse] Warning: {e}")
    finally:
        try:
            close_connection(conn)
        except Exception:
            pass


def _detect_current_workflow(conn):
    """Auto-detect the most recently active workflow from task state."""
    # Prefer in_progress tasks
    row = conn.execute(
        "SELECT workflow_id FROM tasks "
        "WHERE status = 'in_progress' AND workflow_id IS NOT NULL "
        "ORDER BY updated_at DESC LIMIT 1"
    ).fetchone()
    if row:
        return row['workflow_id']
    # Fall back to most recently updated task in any active state
    row = conn.execute(
        "SELECT workflow_id FROM tasks "
        "WHERE status IN ('todo', 'done') AND workflow_id IS NOT NULL "
        "ORDER BY updated_at DESC LIMIT 1"
    ).fetchone()
    return row['workflow_id'] if row else None


def _find_jsonl(args):
    """Locate the target JSONL file."""
    projects_base = os.path.join(
        os.environ.get('USERPROFILE', os.path.expanduser('~')),
        '.claude', 'projects'
    )
    if not os.path.isdir(projects_base):
        return None

    if getattr(args, 'session', None):
        # Search all project dirs for a matching session file
        for entry in _iter_project_dirs(projects_base):
            candidate = os.path.join(entry, f"{args.session}.jsonl")
            if os.path.isfile(candidate):
                return candidate
        # Maybe the session arg is a direct path
        if os.path.isfile(args.session):
            return args.session
        return None

    if getattr(args, 'auto', False):
        return _find_latest_jsonl_for_project(projects_base)

    return None


def _iter_project_dirs(projects_base):
    try:
        for entry in os.scandir(projects_base):
            if entry.is_dir():
                yield entry.path
    except OSError:
        pass


def _find_latest_jsonl_for_project(projects_base):
    """Find the most recently modified JSONL file in the project's Claude dir."""
    import urllib.parse

    cwd = os.getcwd()
    best_mtime = -1
    best_path = None

    # First try to match the current project directory
    target_dir = _find_project_claude_dir(projects_base, cwd)
    search_dirs = [target_dir] if target_dir else list(_iter_project_dirs(projects_base))

    for proj_dir in search_dirs:
        try:
            for fname in os.listdir(proj_dir):
                if not fname.endswith('.jsonl'):
                    continue
                fpath = os.path.join(proj_dir, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                    if mtime > best_mtime:
                        best_mtime = mtime
                        best_path = fpath
                except OSError:
                    pass
        except OSError:
            pass

    return best_path


def _find_project_claude_dir(projects_base, project_path):
    """Find the Claude project hash dir that corresponds to the given path."""
    import urllib.parse

    norm = os.path.normcase(project_path)

    for entry in _iter_project_dirs(projects_base):
        # Try sessions-index.json
        index_file = os.path.join(entry, 'sessions-index.json')
        if os.path.isfile(index_file):
            try:
                with open(index_file, encoding='utf-8') as f:
                    data = json.load(f)
                paths = []
                if isinstance(data, dict):
                    paths.append(data.get('path', ''))
                    paths.extend(data.get('paths', []))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            paths.append(item.get('path', ''))
                        elif isinstance(item, str):
                            paths.append(item)
                for p in paths:
                    if p and os.path.normcase(p) == norm:
                        return entry
            except Exception:
                pass

        # Try URL-decoded directory name
        dir_name = os.path.basename(entry)
        try:
            decoded = urllib.parse.unquote(dir_name)
            if os.path.normcase(decoded) == norm:
                return entry
        except Exception:
            pass

    return None


def _parse_jsonl(jsonl_path):
    """Parse JSONL file and return list of event dicts."""
    events = []
    tool_use_map = {}  # id -> event dict, for duration calculation

    try:
        with open(jsonl_path, encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                _extract_events(obj, events, tool_use_map)
    except OSError as e:
        raise RuntimeError(f"Cannot read {jsonl_path}: {e}")

    return events


def _extract_events(obj, events, tool_use_map):
    """Recursively extract tool_use, tool_result, thinking events from a JSONL object."""
    if not isinstance(obj, dict):
        return

    obj_type = obj.get('type', '')
    timestamp = obj.get('timestamp') or obj.get('event_timestamp') or obj.get('created_at')
    session_id = obj.get('sessionId') or obj.get('session_id')

    # Direct tool_use at top level
    if obj_type == 'tool_use':
        evt = {
            'event_type': 'tool_use',
            'tool_name': obj.get('name'),
            'jsonl_id': obj.get('id'),
            'event_timestamp': timestamp,
            'session_id': session_id,
            'source': 'jsonl',
        }
        events.append(evt)
        if obj.get('id'):
            tool_use_map[obj['id']] = evt
        return

    # Direct tool_result at top level
    if obj_type == 'tool_result':
        tool_use_id = obj.get('tool_use_id')
        result_evt = {
            'event_type': 'tool_result',
            'tool_name': None,
            'jsonl_id': tool_use_id,
            'event_timestamp': timestamp,
            'session_id': session_id,
            'source': 'jsonl',
        }
        # Calculate duration if we have the matching tool_use
        if tool_use_id and tool_use_id in tool_use_map:
            tu = tool_use_map[tool_use_id]
            result_evt['tool_name'] = tu.get('tool_name')
            duration = _calc_duration_ms(tu.get('event_timestamp'), timestamp)
            if duration is not None:
                tu['duration_ms'] = duration
        events.append(result_evt)
        return

    # Direct thinking at top level
    if obj_type == 'thinking':
        events.append({
            'event_type': 'thinking',
            'tool_name': None,
            'jsonl_id': None,
            'event_timestamp': timestamp,
            'session_id': session_id,
            'thinking_tokens': obj.get('thinking_tokens'),
            'source': 'jsonl',
        })
        return

    # Message wrapper (role=assistant or role=user)
    role = obj.get('role', '')
    message = obj.get('message', obj)  # some formats wrap in {"type": "assistant", "message": {...}}
    if obj_type in ('assistant', 'user') and isinstance(obj.get('message'), dict):
        message = obj['message']
        if not session_id:
            session_id = obj.get('sessionId') or obj.get('session_id')
        if not timestamp:
            timestamp = obj.get('timestamp')

    content = message.get('content', []) if isinstance(message, dict) else obj.get('content', [])
    msg_role = message.get('role', role) if isinstance(message, dict) else role
    usage = message.get('usage', {}) if isinstance(message, dict) else {}

    if isinstance(content, list):
        input_tokens = usage.get('input_tokens')
        output_tokens = usage.get('output_tokens')
        for item in content:
            if not isinstance(item, dict):
                continue
            item_type = item.get('type', '')
            if item_type == 'tool_use':
                evt = {
                    'event_type': 'tool_use',
                    'tool_name': item.get('name'),
                    'jsonl_id': item.get('id'),
                    'event_timestamp': timestamp,
                    'session_id': session_id,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'source': 'jsonl',
                }
                events.append(evt)
                if item.get('id'):
                    tool_use_map[item['id']] = evt
            elif item_type == 'tool_result':
                tool_use_id = item.get('tool_use_id')
                result_evt = {
                    'event_type': 'tool_result',
                    'tool_name': None,
                    'jsonl_id': tool_use_id,
                    'event_timestamp': timestamp,
                    'session_id': session_id,
                    'source': 'jsonl',
                }
                if tool_use_id and tool_use_id in tool_use_map:
                    tu = tool_use_map[tool_use_id]
                    result_evt['tool_name'] = tu.get('tool_name')
                    duration = _calc_duration_ms(tu.get('event_timestamp'), timestamp)
                    if duration is not None:
                        tu['duration_ms'] = duration
                events.append(result_evt)
            elif item_type == 'thinking':
                events.append({
                    'event_type': 'thinking',
                    'tool_name': None,
                    'jsonl_id': None,
                    'event_timestamp': timestamp,
                    'session_id': session_id,
                    'thinking_tokens': item.get('thinking_tokens'),
                    'source': 'jsonl',
                })


def _calc_duration_ms(start_ts, end_ts):
    """Calculate millisecond duration between two ISO timestamps."""
    if not start_ts or not end_ts:
        return None
    try:
        start = datetime.fromisoformat(start_ts.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_ts.replace('Z', '+00:00'))
        delta = (end - start).total_seconds() * 1000
        return int(delta) if delta >= 0 else None
    except Exception:
        return None


def _import_events(conn, events, workflow_id_override):
    """Insert parsed events into agent_events. Returns count of inserted rows."""
    inserted = 0
    for evt in events:
        task_id = evt.get('task_id')
        workflow_id = workflow_id_override

        # Backfill workflow_id from task if not overridden
        if not workflow_id and task_id:
            row = conn.execute(
                "SELECT workflow_id FROM tasks WHERE id=?", (task_id,)
            ).fetchone()
            if row:
                workflow_id = row['workflow_id']

        try:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO agent_events "
                "(session_id, workflow_id, task_id, event_type, tool_name, "
                " input_tokens, output_tokens, thinking_tokens, duration_ms, "
                " event_timestamp, jsonl_id, source) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    evt.get('session_id'),
                    workflow_id,
                    task_id,
                    evt.get('event_type'),
                    evt.get('tool_name'),
                    evt.get('input_tokens'),
                    evt.get('output_tokens'),
                    evt.get('thinking_tokens'),
                    evt.get('duration_ms'),
                    evt.get('event_timestamp'),
                    evt.get('jsonl_id'),
                    evt.get('source', 'jsonl'),
                )
            )
            inserted += cursor.rowcount
        except Exception:
            pass

    return inserted


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def handle_report(args):
    conn = get_db(args)
    try:
        workflow_filter = getattr(args, 'workflow', None)
        wf_clause = " AND workflow_id=?" if workflow_filter else ""
        wf_params = [workflow_filter] if workflow_filter else []

        rows = conn.execute(
            f"SELECT tool_name, COUNT(*) as cnt, "
            f"AVG(duration_ms) as avg_ms "
            f"FROM agent_events "
            f"WHERE event_type='tool_use' {wf_clause} "
            f"GROUP BY tool_name ORDER BY cnt DESC",
            wf_params
        ).fetchall()

        if not rows:
            print("No tool_use events recorded yet.")
            return

        total_calls = sum(r['cnt'] for r in rows)
        header = "Tool Usage Report"
        if workflow_filter:
            header += f" [workflow: {workflow_filter}]"
        print(header)
        print(f"{'Tool':<30} {'Calls':>6} {'Avg ms':>8} {'%':>6}")
        print("-" * 55)
        for r in rows:
            name = r['tool_name'] or '(unknown)'
            pct = (r['cnt'] / total_calls * 100) if total_calls else 0
            avg = f"{r['avg_ms']:.0f}" if r['avg_ms'] is not None else "N/A"
            print(f"{name:<30} {r['cnt']:>6} {avg:>8} {pct:>5.1f}%")
        print("-" * 55)
        print(f"{'Total':<30} {total_calls:>6}")

        # Supplementary stats
        think_count = conn.execute(
            f"SELECT COUNT(*) as c FROM agent_events "
            f"WHERE event_type='thinking' {wf_clause}",
            wf_params
        ).fetchone()['c']

        subagent_count = conn.execute(
            f"SELECT COUNT(*) as c FROM agent_events "
            f"WHERE event_type='subagent_start' {wf_clause}",
            wf_params
        ).fetchone()['c']

        token_row = conn.execute(
            f"SELECT SUM(input_tokens) as tin, SUM(output_tokens) as tout, "
            f"SUM(thinking_tokens) as tthink "
            f"FROM agent_events WHERE source='jsonl' {wf_clause}",
            wf_params
        ).fetchone()

        print()
        print(f"Thinking events  : {think_count}")
        print(f"Subagent launches: {subagent_count}")
        if token_row['tin'] is not None or token_row['tout'] is not None:
            print(f"Tokens (JSONL)   : input={token_row['tin'] or 0} "
                  f"output={token_row['tout'] or 0} "
                  f"thinking={token_row['tthink'] or 0}")
    finally:
        close_connection(conn)


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def handle_summary(args):
    conn = get_db(args)
    try:
        session_filter = getattr(args, 'session', None)

        if not session_filter:
            row = conn.execute(
                "SELECT session_id FROM agent_events "
                "WHERE session_id IS NOT NULL "
                "ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            if not row:
                print("No session data found.")
                return
            session_filter = row['session_id']

        bounds = conn.execute(
            "SELECT MIN(event_timestamp) as first_ts, MAX(event_timestamp) as last_ts, "
            "COUNT(*) as total_events "
            "FROM agent_events WHERE session_id=?",
            (session_filter,)
        ).fetchone()

        if not bounds or bounds['total_events'] == 0:
            print(f"No events found for session: {session_filter}")
            return

        duration_str = "N/A"
        if bounds['first_ts'] and bounds['last_ts']:
            ms = _calc_duration_ms(bounds['first_ts'], bounds['last_ts'])
            if ms is not None:
                secs = ms / 1000
                duration_str = f"{int(secs // 60)}m {int(secs % 60)}s"

        print(f"Session: {session_filter}")
        print(f"Duration: {duration_str}  (from {bounds['first_ts']} to {bounds['last_ts']})")
        print(f"Total events: {bounds['total_events']}")
        print()

        # Top 3 tools
        top_tools = conn.execute(
            "SELECT tool_name, COUNT(*) as cnt FROM agent_events "
            "WHERE session_id=? AND event_type='tool_use' AND tool_name IS NOT NULL "
            "GROUP BY tool_name ORDER BY cnt DESC LIMIT 3",
            (session_filter,)
        ).fetchall()
        if top_tools:
            print("Top tools:")
            for t in top_tools:
                print(f"  {t['tool_name']}: {t['cnt']} calls")

        # Thinking + subagent
        think = conn.execute(
            "SELECT COUNT(*) as c FROM agent_events "
            "WHERE session_id=? AND event_type='thinking'",
            (session_filter,)
        ).fetchone()['c']
        subagent = conn.execute(
            "SELECT COUNT(*) as c FROM agent_events "
            "WHERE session_id=? AND event_type='subagent_start'",
            (session_filter,)
        ).fetchone()['c']
        print(f"Thinking events: {think}")
        print(f"Subagent launches: {subagent}")
        print()

        # Linked workflows and tasks
        workflows = conn.execute(
            "SELECT DISTINCT workflow_id FROM agent_events "
            "WHERE session_id=? AND workflow_id IS NOT NULL",
            (session_filter,)
        ).fetchall()
        if workflows:
            print("Linked workflows:")
            for w in workflows:
                print(f"  {w['workflow_id']}")

        tasks = conn.execute(
            "SELECT DISTINCT task_id FROM agent_events "
            "WHERE session_id=? AND task_id IS NOT NULL",
            (session_filter,)
        ).fetchall()
        if tasks:
            print("Linked tasks:")
            for t in tasks:
                print(f"  {t['task_id']}")
    finally:
        close_connection(conn)
