"""TaskOps CLI entry point.
TaskOps CLI 진입점. argparse 기반 서브커맨드 라우팅.
"""
import argparse
import sys

__version__ = "0.2.6"


def build_parser():
    parser = argparse.ArgumentParser(
        prog='taskops',
        description='TaskOps - AI Agent project management tool (ETS-based)'
    )
    parser.add_argument('--version', action='version', version=f'taskops {__version__}')
    parser.add_argument('--db', type=str, default=None,
                        help='Path to SQLite DB file')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    from .commands.init import register as register_init
    from .commands.epic import register as register_epic
    from .commands.task import register as register_task
    from .commands.objective import register as register_objective
    from .commands.workflow import register as register_workflow
    from .commands.operation import register as register_operation
    from .commands.resource import register as register_resource
    from .commands.query import register as register_query
    from .commands.setting import register as register_setting
    from .commands.project import register as register_project
    from .commands.plan import register as register_plan

    register_init(subparsers)
    register_epic(subparsers)
    register_task(subparsers)
    register_objective(subparsers)
    register_workflow(subparsers)
    register_operation(subparsers)
    register_resource(subparsers)
    register_query(subparsers)
    register_setting(subparsers)
    register_project(subparsers)
    register_plan(subparsers)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()
