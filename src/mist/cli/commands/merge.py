import argparse
from ... import Mist

# TODO: -s <strategy> --strategy=<strategy>, -X <option> --strategy-option=<option>, -q --quiet, -v --verbose, --[no-]progress, --allow-unrelated-histories, --abort, --quit, --continue,

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("merge", description="Join objects from two or more repositories")
    parser.add_argument("remote", metavar="<remote>", nargs="?")

    def func(args):
        raise NotImplementedError

    parser.set_defaults(func=func, parser=parser)
    return parser