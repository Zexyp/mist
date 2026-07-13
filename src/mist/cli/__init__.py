#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import argparse
import configparser
import os
import sys
import warnings

from ..log import announce_optional_module_error

try:
    import argcomplete
except ImportError as e:
    argcomplete = None
    announce_optional_module_error(e)

from .commands import merge
from .. import Mist, _package_name
from ..errors import MistError
from .. import config
from ..messages import *

# TODO: pad to multiples

# TODO: --config-env=<name>=<envvar>, docs paths, -p --paginate, -P --no-pager, --work-tree=<path>, --no-lazy-fetch, --no-advice,
# TODO: commands
"""
status, diff, submodule, tag, restore
add
rm
gc
restore
ls-files
ignore
"""

class HelpAction(argparse.Action):
    def __init__(self, option_strings, dest, commands=None, **kwargs):
        self.commands = commands
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if option_string == "-h":
            parser.print_usage()
            parser.exit()
        if option_string == "--help":
            parser.print_help()
            print("commands:")
            for name, subparser in self.commands.items():
                print(f"  {name:16}", end="")
                if subparser.description:
                    print(f" {subparser.description}", end="")
                print()

            parser.exit()

        # default to error
        parser.print_usage()
        parser.exit(1)

def build_parser(mist: Mist) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False, description="another stupid content tracker")

    subparsers = parser.add_subparsers(metavar="<command>", dest="command")

    from .commands import help as cmd_help
    from .commands import init, config, remote, fetch, merge, clone, ls_remote, ls_files, pull
    command_parsers = {
        "help": cmd_help.build_parser(subparsers, mist),
        "config": config.build_parser(subparsers, mist),
        "init": init.build_parser(subparsers, mist),
        "clone": clone.build_parser(subparsers, mist),
        "remote": remote.build_parser(subparsers, mist),
        "fetch": fetch.build_parser(subparsers, mist),
        "merge": merge.build_parser(subparsers, mist),
        "pull": pull.build_parser(subparsers, mist),
        "ls-remote": ls_remote.build_parser(subparsers, mist),
        "ls-files": ls_files.build_parser(subparsers, mist),
    }

    def parse_configuration_param(arg: str) -> tuple[str, str]:
        SPLIT_BY = "="
        if  SPLIT_BY not in arg:
            parser.error("malformed configuration arg")
        parts = arg.split(SPLIT_BY, 1)
        return parts[0].strip(), parts[1].strip()

    from importlib.metadata import version
    parser.add_argument("-v", "--version", action="version", version=f"Mist {version(_package_name)}")
    help_group = parser.add_mutually_exclusive_group(required=False)
    help_group.add_argument("-h", action=HelpAction, nargs=0, help="short help", commands=command_parsers)
    help_group.add_argument("--help", action=HelpAction, nargs=0, help="extensive help", commands=command_parsers)
    parser.add_argument("-C", metavar="<path>")
    parser.add_argument("-c", metavar="<name>=<value>", action="append", type=parse_configuration_param)
    parser.add_argument("--mist-dir", metavar="<path>", default=None)

    #parser_checkout = subparsers.add_parser("checkout")
    #parser_checkout.add_argument("remote")
    #parser_checkout.set_defaults(func=lambda args: checkout(remote=args.remote))
    ## parser_diff = subparsers.add_parser("diff")
    ## parser_submodule = subparsers.add_parser("submodule")
    #parser_tag = subparsers.add_parser("tag")
    #parser_tag.set_defaults(func=lambda args: tag())
    #parser_diff = subparsers.add_parser("diff")
    #parser_rm = subparsers.add_parser("rm")
    #parser_restore = subparsers.add_parser("restore")

    #parser_list = subparsers.add_parser("list", aliases=["ls"])
    #parser_list.add_argument("remote", nargs='?')
    #parser_list.add_argument("--verbose", action="store_true", dest="list_verbose")
    #parser_list.set_defaults(func=lambda args: list_entries(args.remote, verbose=args.list_verbose))

    parser.set_defaults(parser=parser)
    return parser


def run(arguments: list[str]):
    mist = Mist()
    parser = build_parser(mist)

    args = parser.parse_args(arguments)

    previous_dir = None
    if args.C:
        if not os.path.isdir(args.C):
            raise MistError(MSG_CD_NO_SUCH_DIR.format(directory=args.C))
        previous_dir = os.getcwd()
        os.chdir(args.C)

    if args.c:
        mist.config.args.settings = {t[0]: t[1] for t in args.c}
        mist.config.args.commit()

    mist.set_working_dir(os.getcwd())
    if args.mist_dir:
        mist.set_repository_dir(args.mist_dir)

    if argcomplete:
        argcomplete.autocomplete(parser, always_complete_options=False)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        if hasattr(args, "parser"):
            args.parser.print_usage()
        else:
            parser.print_usage()
        parser.exit(1)

    if previous_dir:
        os.chdir(previous_dir)
