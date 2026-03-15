"""Resource management command.
Resource 관리 커맨드.
"""


def register(subparsers):
    parser = subparsers.add_parser('resource', help='Manage resources')
    sub = parser.add_subparsers(dest='subcommand')

    add = sub.add_parser('add', help='Add a resource')
    add.add_argument('task_id', help='Task ID')
    add.add_argument('--path', required=True, help='File path')
    add.add_argument('--type', choices=['input', 'output', 'reference', 'intermediate'],
                     default='reference', help='Resource type')
    add.add_argument('--desc', default='', help='Description')
    add.set_defaults(func=handle)

    lst = sub.add_parser('list', help='List resources')
    lst.add_argument('--task', help='Filter by task ID')
    lst.add_argument('--type', help='Filter by type')
    lst.set_defaults(func=handle)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle(args):
    print("resource: not yet implemented")
