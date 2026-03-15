"""Project initialization command.
프로젝트 초기화 커맨드.
"""


def register(subparsers):
    parser = subparsers.add_parser('init', help='Initialize a new project')
    parser.add_argument('--name', required=True, help='Project name')
    parser.add_argument('--prefix', required=True, help='Task ID prefix (e.g. TOS)')
    parser.add_argument('--path', default='.', help='Project folder path (default: cwd)')
    parser.set_defaults(func=handle)


def handle(args):
    print("init: not yet implemented")
