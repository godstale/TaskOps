"""Task/SubTask management command.
Task/SubTask 관리 커맨드.
"""


def register(subparsers):
    parser = subparsers.add_parser('task', help='Manage tasks')
    sub = parser.add_subparsers(dest='subcommand')

    create = sub.add_parser('create', help='Create a new task')
    create.add_argument('--parent', required=True, help='Parent ID (Epic or Task)')
    create.add_argument('--title', required=True, help='Task title')
    create.add_argument('--description', default='', help='Task description')
    create.add_argument('--todo', default='', help='Todo checklist (markdown)')
    create.set_defaults(func=handle)

    lst = sub.add_parser('list', help='List tasks')
    lst.add_argument('--epic', help='Filter by epic ID')
    lst.add_argument('--parent', help='Filter by parent ID')
    lst.add_argument('--status', help='Filter by status')
    lst.set_defaults(func=handle)

    show = sub.add_parser('show', help='Show task details')
    show.add_argument('id', help='Task ID')
    show.set_defaults(func=handle)

    update = sub.add_parser('update', help='Update a task')
    update.add_argument('id', help='Task ID')
    update.add_argument('--status', help='New status')
    update.add_argument('--title', help='New title')
    update.add_argument('--description', help='New description')
    update.add_argument('--todo', help='New todo checklist')
    update.add_argument('--interrupt', help='Interrupt reason')
    update.set_defaults(func=handle)

    delete = sub.add_parser('delete', help='Delete a task')
    delete.add_argument('id', help='Task ID')
    delete.set_defaults(func=handle)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle(args):
    print("task: not yet implemented")
