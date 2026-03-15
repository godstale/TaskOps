"""Operation logging command.
Operations 기록 커맨드.
"""


def register(subparsers):
    parser = subparsers.add_parser('op', help='Log operations')
    sub = parser.add_subparsers(dest='subcommand')

    start = sub.add_parser('start', help='Record task start')
    start.add_argument('task_id', help='Task ID')
    start.add_argument('--platform', default='unknown', help='Agent platform')
    start.set_defaults(func=handle)

    progress = sub.add_parser('progress', help='Record progress')
    progress.add_argument('task_id', help='Task ID')
    progress.add_argument('--summary', required=True, help='Progress summary')
    progress.add_argument('--details', help='Details (JSON)')
    progress.add_argument('--subagent', action='store_true', help='Sub agent used')
    progress.set_defaults(func=handle)

    complete = sub.add_parser('complete', help='Record task completion')
    complete.add_argument('task_id', help='Task ID')
    complete.add_argument('--summary', required=True, help='Completion summary')
    complete.add_argument('--details', help='Details (JSON)')
    complete.set_defaults(func=handle)

    error = sub.add_parser('error', help='Record error')
    error.add_argument('task_id', help='Task ID')
    error.add_argument('--summary', required=True, help='Error summary')
    error.set_defaults(func=handle)

    interrupt = sub.add_parser('interrupt', help='Record interruption')
    interrupt.add_argument('task_id', help='Task ID')
    interrupt.add_argument('--summary', required=True, help='Interrupt reason')
    interrupt.set_defaults(func=handle)

    log = sub.add_parser('log', help='Show operation log')
    log.add_argument('--task', help='Filter by task ID')
    log.set_defaults(func=handle)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle(args):
    print("op: not yet implemented")
