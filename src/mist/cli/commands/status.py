import argparse

from ..cli_utils import summon_subcommand
from ... import Mist

# TODO: -v --[no-]verbose, -s --[no-]short, -b --[no-]branch, --[no-]show-stash, --[no-]long (default), -u --[no-]untracked-files=[<mode>], --[no-]ignored, --[no-]ignore-submodules, --[no-]renames

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = summon_subcommand(subparsers, "status", description="Show the working tree status")

    def func(args):
        raise NotImplementedError
        print("Changes:")
        print("Untracked files:")

    parser.set_defaults(func=func, parser=parser)
    return parser
