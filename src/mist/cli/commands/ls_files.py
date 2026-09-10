import argparse
import warnings

from ..cli_utils import summon_subcommand
from ... import Mist

# TODO: --full-name, --[no-]recursive-submodules, --[no-]duplicate

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = summon_subcommand(subparsers, "ls-files")
    parser.add_argument("-c", "--cached", action='store_true', default=None)
    parser.add_argument("-d", "--deleted", action='store_true', default=None)
    parser.add_argument("-m", "--modified", action='store_true', default=None)
    parser.add_argument("-o", "--others", action='store_true', default=None)
    parser.add_argument("-i", "--ignored", action='store_true', default=None)
    parser.add_argument("-u", "--unmerged", action='store_true', default=None)

    def func(args):
        for e in mist.list_files():
            print(e)

    parser.set_defaults(func=func, parser=parser)

    return parser