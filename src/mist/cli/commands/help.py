import argparse
from ... import Mist

# TODO: -a --all, --[no-]aliases, -c

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("help")
    parser.add_argument("command", metavar="<command>", nargs="?")

    def func(args):
        raise NotImplementedError

    parser.set_defaults(func=func, parser=parser)
    return parser