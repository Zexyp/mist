import argparse
import configparser
import os
import sys

from .. import Mist, _package_name
from ..errors import MistError
from .. import log
from .. import config

LOG_VERBOSE = False
LOG_DEBUG = False

def _parse_configuration_param(arg: str) -> tuple[str, str]:
    SPLIT_BY = "="
    assert SPLIT_BY in arg
    parts = arg.split(SPLIT_BY, 1)
    return parts[0], parts[1]

def build_parser(mist: Mist) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    from importlib.metadata import version
    parser.add_argument("-v", "--version", action="version", version=f"Mist {_package_name}")
    parser.add_argument("-C", metavar="<path>")
    parser.add_argument("-c", metavar="<name>=<value>", action="append", type=_parse_configuration_param)
    parser.add_argument("--mist-dir", metavar="<path>", default=None)

    subparsers = parser.add_subparsers(metavar="<command>", dest="command")

    from .commands import init, remote, fetch, status, clone, pull, config#, checkout, merge, diff, submodule, tag, rm, restore
    init.build_parser(subparsers, mist)
    config.build_parser(subparsers, mist)
    remote.build_parser(subparsers, mist)
    fetch.build_parser(subparsers, mist)
    clone.build_parser(subparsers, mist)
    pull.build_parser(subparsers, mist)
    status.build_parser(subparsers, mist)

    #parser_checkout = subparsers.add_parser("checkout")
    #parser_checkout.add_argument("remote")
    #parser_checkout.set_defaults(func=lambda args: checkout(remote=args.remote))
    #parser_merge = subparsers.add_parser("merge")
    #parser_merge.add_argument("remote")
    #parser_merge.set_defaults(func=lambda args: merge(remote=args.remote))
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

    return parser

def _internal_run():
    mist = Mist()
    parser = build_parser(mist)

    args = parser.parse_args()

    previous_dir = None
    if args.C:
        if not os.path.isdir(args.C):
            raise MistError(f"cannot change to '{args.C}': No such directory")
        previous_dir = os.getcwd()
        os.chdir(args.C)

    if args.c:
        mist.config.args.settings = {t[0]: t[1] for t in args.c}
        mist.config.args.commit()

    mist.set_working_dir(os.getcwd())
    if args.mist_dir:
        mist.set_repository_dir(args.mist_dir)

    log.configure(mist.config.active)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        if hasattr(args, "parser"):
            args.parser.print_help()
        else:
            parser.print_help()
        exit(1)

    if previous_dir:
        os.chdir(previous_dir)

def run():
    try:
        _internal_run()
    except MistError as e:
        log.exception(e)
        log.error(str(e))
        sys.exit(1)
    except NotImplementedError as e:
        log.exception(e)
        log.fatal(f"{type(e).__name__}: {str(e)}")
        log.fatal("lazy fuck detected")
        sys.exit(1)
    except Exception as e:
        log.exception(e)
        log.fatal(f"{type(e).__name__}: {str(e)}")
        log.fatal("unrecoverable error")
        sys.exit(1)