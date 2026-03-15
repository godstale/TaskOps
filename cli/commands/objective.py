"""Objective management command.
Objective 관리 커맨드.
"""


def register(subparsers):
    parser = subparsers.add_parser('objective', help='Manage objectives')
    sub = parser.add_subparsers(dest='subcommand')

    create = sub.add_parser('create', help='Create a new objective')
    create.add_argument('--title', required=True, help='Objective title')
    create.add_argument('--milestone', help='Milestone target description')
    create.add_argument('--due-date', help='Due date (YYYY-MM-DD)')
    create.set_defaults(func=handle)

    lst = sub.add_parser('list', help='List all objectives')
    lst.set_defaults(func=handle)

    update = sub.add_parser('update', help='Update an objective')
    update.add_argument('id', help='Objective ID')
    update.add_argument('--status', help='New status')
    update.add_argument('--title', help='New title')
    update.set_defaults(func=handle)

    delete = sub.add_parser('delete', help='Delete an objective')
    delete.add_argument('id', help='Objective ID')
    delete.set_defaults(func=handle)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle(args):
    print("objective: not yet implemented")
