import argparse
from ... import Mist

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("pull")
    parser.add_argument("remote", nargs='?')
    parser.add_argument("--set-upstream", action="store_true")
    parser.set_defaults(func=lambda args: pull(args.remote, set_upstream=args.set_upstream))

    return parser