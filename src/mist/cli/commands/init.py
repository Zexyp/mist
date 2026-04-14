import argparse
import os

from ... import Mist, MistError

# TODO: -q --quiet

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("init")

    def func(args):
        target = mist.init(args.directory or os.getcwd())
        print(f"Initialized empty Mist repository in {target}")

    parser.set_defaults(func=func, parser=parser)
    parser.add_argument("directory", metavar="<directory>", nargs="?")

    return parser
