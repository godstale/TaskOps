"""Status query and report generation command.
상태 조회 및 리포트 생성 커맨드.
"""


def register(subparsers):
    parser = subparsers.add_parser('query', help='Query status and generate reports')
    sub = parser.add_subparsers(dest='subcommand')

    status = sub.add_parser('status', help='Show project status summary')
    status.set_defaults(func=handle)

    tasks = sub.add_parser('tasks', help='List tasks by filter')
    tasks.add_argument('--status', help='Filter by status')
    tasks.set_defaults(func=handle)

    gen_todo = sub.add_parser('generate-todo', help='Regenerate TODO.md from DB')
    gen_todo.set_defaults(func=handle)

    gen_ops = sub.add_parser('generate-ops', help='Regenerate TASK_OPERATIONS.md from DB')
    gen_ops.set_defaults(func=handle)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle(args):
    print("query: not yet implemented")
