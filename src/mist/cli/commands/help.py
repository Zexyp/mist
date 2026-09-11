import argparse

from ..cli_utils import summon_subcommand
from ... import Mist
from ..completors import HelpCompleter

# TODO: -a --all, --[no-]aliases, -c

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = summon_subcommand(subparsers, "help")
    parser.add_argument("topic", nargs="?").completer = HelpCompleter()

    def func(args):
        parser.error("not implemented: use -h/--help")
        raise NotImplementedError

    parser.set_defaults(func=func, parser=parser)
    return parser