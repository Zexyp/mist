import argparse
import warnings

from ... import Mist

def build_parser_add(subparsers, mist: Mist):
    parser = subparsers.add_parser("add")
    parser.add_argument("name", metavar="<name>")
    parser.add_argument("url", metavar="<url>")

    def func(args):
        mist.remote_add(args.name, args.url)

    parser.set_defaults(func=func, parser=parser)
    return parser


def build_parser_rename(subparsers, mist: Mist):
    parser = subparsers.add_parser("rename")
    parser.add_argument("old", metavar="<old>")
    parser.add_argument("new", metavar="<new>")

    def func(args):
        mist.remote_rename(args.old, args.new)

    parser.set_defaults(func=func, parser=parser)
    return parser

def build_parser_remove(subparsers, mist: Mist):
    parser = subparsers.add_parser("remove", aliases=["rm"])
    parser.add_argument("name", metavar="<name>")

    def func(args):
        raise NotImplementedError

    parser.set_defaults(func=func, parser=parser)
    return parser

def build_parser_get_url(subparsers, mist: Mist):
    parser = subparsers.add_parser("get-url")
    parser.add_argument("name", metavar="<name>")

    def func(args):
        mist.remote_remove(args.name)

    parser.set_defaults(func=func, parser=parser)
    return parser

def build_parser_set_url(subparsers, mist: Mist):
    parser = subparsers.add_parser("set-url")
    parser.add_argument("name", metavar="<name>")
    parser.add_argument("newurl", metavar="<newurl>")

    def func(args):
        mist.remote_set_url(args.name, args.newurl)

    parser.set_defaults(func=func, parser=parser)
    return parser

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("remote")
    parser.add_argument("-v", "--verbose", action="store_true")

    def func(args):
        for name in mist.remotes_list():
            line = name
            if args.verbose:
                line = f"{line:<7} {mist.config.active.get(f"remote.{name}.url", None)}"

            print(line)

    parser.set_defaults(func=func, parser=parser)

    subparsers_remote = parser.add_subparsers()

    build_parser_add(subparsers_remote, mist)
    build_parser_rename(subparsers_remote, mist)
    build_parser_remove(subparsers_remote, mist)
    build_parser_get_url(subparsers_remote, mist)
    build_parser_set_url(subparsers_remote, mist)

    return parser