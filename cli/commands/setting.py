"""Setting management command.
설정 관리 커맨드.
"""


def register(subparsers):
    parser = subparsers.add_parser('setting', help='Manage settings')
    sub = parser.add_subparsers(dest='subcommand')

    s = sub.add_parser('set', help='Set a setting value')
    s.add_argument('key', help='Setting key')
    s.add_argument('value', help='Setting value')
    s.add_argument('--desc', default='', help='Description')
    s.set_defaults(func=handle)

    g = sub.add_parser('get', help='Get a setting value')
    g.add_argument('key', help='Setting key')
    g.set_defaults(func=handle)

    lst = sub.add_parser('list', help='List all settings')
    lst.set_defaults(func=handle)

    d = sub.add_parser('delete', help='Delete a setting')
    d.add_argument('key', help='Setting key')
    d.set_defaults(func=handle)

    parser.set_defaults(func=lambda args: parser.print_help())


def handle(args):
    print("setting: not yet implemented")
