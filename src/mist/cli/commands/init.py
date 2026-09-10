import argparse
import os

from ..cli_utils import summon_subcommand
from ... import Mist, MistError

# TODO: -q --quiet

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = summon_subcommand(subparsers, "init", description="Create an empty Mist repository")
    parser.add_argument("directory", metavar="<directory>", nargs="?")

    def func(args):
        target = mist.init(args.directory or os.getcwd())
        print(f"Initialized empty Mist repository in {target}")

    parser.set_defaults(func=func, parser=parser)

    return parser
