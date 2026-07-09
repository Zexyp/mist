import argparse
from ... import Mist
from ..completors import HelpCompleter

# TODO: -a --all, --[no-]aliases, -c

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("help", add_help=False)
    parser.add_argument("topic", nargs="?").completer = HelpCompleter()

    def func(args):
        parser.error("use -h/--help")
        raise NotImplementedError

    parser.set_defaults(func=func, parser=parser)
    return parser