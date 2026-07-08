import argparse

from ... import Mist


def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("ls-files")

    def func(args):
        raise NotImplementedError

    parser.set_defaults(func=func, parser=parser)

    return parser