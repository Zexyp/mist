import argparse
import sys
import traceback
from tabnanny import verbose

from . import *
from . import shenanigans
from . import log
from . import core

def _parse_on_off(value: str | None) -> bool | None:
    match value:
        case 'on': return True
        case 'off': return False
        case _: return None

def build_parser_remote(subparsers):
    parser = subparsers.add_parser("remote")
    parser.add_argument("-v", "--verbose", action="store_true", dest="remote_verbose",)
    parser.set_defaults(func=lambda args: remote_list(args.remote_verbose))

    subparsers_remote = parser.add_subparsers()

    parser_add = subparsers_remote.add_parser("add")
    parser_add.add_argument("name")
    parser_add.add_argument("url")
    parser_add.set_defaults(func=lambda args: remote_add(args.name, args.url))

    parser_set_url = subparsers_remote.add_parser("set-url")
    parser_set_url.add_argument("name")
    parser_set_url.add_argument("newurl")
    parser_set_url.set_defaults(func=lambda args: remote_set_url(args.name, args.newurl))

    parser_remove = subparsers_remote.add_parser("remove", aliases=["rm"])
    parser_remove.add_argument("name")
    parser_remove.set_defaults(func=lambda args: remote_remove(args.name))

    return parser

def build_parser_fetch(subparsers):
    parser = subparsers.add_parser("fetch")
    parser.add_argument("remote", nargs='?')
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--set-upstream", action="store_true")
    parser.add_argument("--tags", action="store_true")
    parser.set_defaults(func=lambda args: fetch(args.remote, all=args.all, set_upstream=args.set_upstream, tags=args.tags))

    return parser

def build_parser_pull(subparsers):
    parser = subparsers.add_parser("pull")
    parser.add_argument("remote", nargs='?')
    parser.add_argument("--set-upstream", action="store_true")
    parser.set_defaults(func=lambda args: pull(args.remote, set_upstream=args.set_upstream))

    return parser

def build_parser_clone(subparsers):
    parser = subparsers.add_parser("clone")
    parser.add_argument("url")
    parser.add_argument("dir", nargs='?')
    parser.add_argument("--origin")
    parser.set_defaults(func=lambda args: clone(args.url, output=args.dir, origin=args.origin))

    return parser

def build_parser_config(subparsers):
    parser = subparsers.add_parser("config")  # locations: global, system, local, worktree?
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--local", dest="kind", action="store_const", const="local")
    group.add_argument("--forced", dest="kind", action="store_const", const="forced")
    group.add_argument("--global", dest="kind", action="store_const", const="global")
    #group.add_argument("--system", dest="kind", action="store_const", const="system")
    parser.add_argument("key", nargs='?')
    parser.add_argument("value", nargs='?')
    parser.add_argument("--list", "-l", action="store_true")
    parser.add_argument("--edit", action="store_true")
    parser.add_argument("--unset", action="store_true")
    parser.set_defaults(func=lambda args: config(key=args.key, value=args.value, kind=args.kind,
                                                 # operations
                                                 list=args.list,
                                                 edit=args.edit,
                                                 unset=args.unset))

    return parser

def build_parser():
    # TODO: subparser verbosity?
    parser = argparse.ArgumentParser()

    from importlib.metadata import version
    parser.add_argument("--version", action="version", version=f"Mist {version(__package__)}")
    parser.add_argument("--debug", action="store_true", default=None)
    parser.add_argument("--verbose", action="store_true", default=None)
    parser.add_argument("--color", choices=["auto", "off", "force"])
    parser.add_argument("--sound", choices=["on", "off"])
    parser.add_argument("-C")

    subparsers = parser.add_subparsers()

    parser_init = subparsers.add_parser("init")
    parser_init.set_defaults(func=lambda args: init())
    parser_remote = build_parser_remote(subparsers)
    parser_fetch = build_parser_fetch(subparsers)
    parser_status = subparsers.add_parser("status")
    parser_status.set_defaults(func=lambda args: status())
    parser_checkout = subparsers.add_parser("checkout")
    parser_checkout.add_argument("remote")
    parser_checkout.set_defaults(func=lambda args: checkout(remote=args.remote))
    parser_clone = build_parser_clone(subparsers)
    parser_merge = subparsers.add_parser("merge")
    parser_merge.add_argument("remote")
    parser_merge.set_defaults(func=lambda args: merge(remote=args.remote))
    parser_pull = build_parser_pull(subparsers)
    #parser_diff = subparsers.add_parser("diff")
    #parser_submodule = subparsers.add_parser("submodule")
    parser_config = build_parser_config(subparsers)
    parser_tag = subparsers.add_parser("tag")
    parser_tag.set_defaults(func=lambda args: tag())

    parser_list = subparsers.add_parser("list", aliases=["ls"])
    parser_list.add_argument("remote", nargs='?')
    parser_list.add_argument("--verbose", action="store_true", dest="list_verbose")
    parser_list.set_defaults(func=lambda args: list_entries(args.remote, verbose=args.list_verbose))

    return parser

def run():
    parser = build_parser()

    args = parser.parse_args()
    prev_dir = None
    if args.C:
        assert os.path.isdir(args.C)
        prev_dir = os.getcwd()
        os.chdir(args.C)

    core.configure(debug=args.debug,
                   verbose=args.verbose,
                   color=args.color,
                   sound=_parse_on_off(args.sound))

    core.apply_configuration()

    core.initialize()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

    if prev_dir:
        os.chdir(prev_dir)
