"""TaskOps CLI entry point.
TaskOps CLI 진입점. argparse 기반 서브커맨드 라우팅.
"""
import argparse
import sys

__version__ = "0.2.6"


def build_parser():
    # Shared base parser for arguments that should be available to all commands
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('--db', type=str, default=None,
                        help='Path to SQLite DB file')

    parser = argparse.ArgumentParser(
        prog='taskops',
        description='TaskOps - AI Agent project management tool (ETS-based)',
        parents=[base_parser]
    )
    parser.add_argument('--version', action='version', version=f'taskops {__version__}')

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

    # Register each subcommand with the shared base_parser to allow --db after the command
    def register_with_base(register_func, subparsers):
        # We need to wrap the add_parser call or modify the register functions.
        # Modifying register functions is cleaner for future additions.
        register_func(subparsers, [base_parser])

    register_init(subparsers, [base_parser])
    register_epic(subparsers, [base_parser])
    register_task(subparsers, [base_parser])
    register_objective(subparsers, [base_parser])
    register_workflow(subparsers, [base_parser])
    register_operation(subparsers, [base_parser])
    register_resource(subparsers, [base_parser])
    register_query(subparsers, [base_parser])
    register_setting(subparsers, [base_parser])
    register_project(subparsers, [base_parser])
    register_plan(subparsers, [base_parser])

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
