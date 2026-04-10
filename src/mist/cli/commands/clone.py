import argparse
from ... import Mist

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("clone")
    parser.add_argument("url")
    parser.add_argument("dir", nargs='?')
    parser.add_argument("--origin")
    parser.set_defaults(func=lambda args: clone(args.url, output=args.dir, origin=args.origin))

    return parser