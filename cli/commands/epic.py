"""Epic management command.
Epic 관리 커맨드.
"""


def register(subparsers):
    parser = subparsers.add_parser('epic', help='Manage epics')
    sub = parser.add_subparsers(dest='subcommand')

    create = sub.add_parser('create', help='Create a new epic')
    create.add_argument('--title', required=True, help='Epic title')
    create.add_argument('--description', default='', help='Epic description')
    create.set_defaults(func=handle)

    lst = sub.add_parser('list', help='List all epics')
    lst.set_defaults(func=handle)

    show = sub.add_parser('show', help='Show epic details')
    show.add_argument('id', help='Epic ID')
    show.set_defaults(func=handle)

    update = sub.add_parser('update', help='Update an epic')
    update.add_argument('id', help='Epic ID')
    update.add_argument('--status', help='New status')
    update.add_argument('--title', help='New title')
    update.add_argument('--description', help='New description')
    update.set_defaults(func=handle)

    delete = sub.add_parser('delete', help='Delete an epic')
    delete.add_argument('id', help='Epic ID')
    delete.set_defaults(func=handle)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle(args):
    print("epic: not yet implemented")
