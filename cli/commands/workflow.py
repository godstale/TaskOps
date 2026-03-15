"""Workflow management command.
Workflow 관리 커맨드.
"""


def register(subparsers):
    parser = subparsers.add_parser('workflow', help='Manage workflow')
    sub = parser.add_subparsers(dest='subcommand')

    set_order = sub.add_parser('set-order', help='Set task execution order')
    set_order.add_argument('task_ids', nargs='+', help='Task IDs in order')
    set_order.set_defaults(func=handle)

    set_parallel = sub.add_parser('set-parallel', help='Set parallel execution group')
    set_parallel.add_argument('--group', required=True, help='Group name')
    set_parallel.add_argument('task_ids', nargs='+', help='Task IDs')
    set_parallel.set_defaults(func=handle)

    add_dep = sub.add_parser('add-dep', help='Add dependency')
    add_dep.add_argument('task_id', help='Task ID')
    add_dep.add_argument('--depends-on', nargs='+', required=True, help='Dependency task IDs')
    add_dep.set_defaults(func=handle)

    show = sub.add_parser('show', help='Show workflow')
    show.set_defaults(func=handle)

    nxt = sub.add_parser('next', help='Show next executable tasks')
    nxt.set_defaults(func=handle)

    current = sub.add_parser('current', help='Show currently active task')
    current.set_defaults(func=handle)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle(args):
    print("workflow: not yet implemented")
