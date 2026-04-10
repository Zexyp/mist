import argparse
from ... import Mist

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("fetch")
    parser.add_argument("remote", nargs='?')
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--set-upstream", action="store_true")
    parser.add_argument("--tags", action="store_true")
    parser.set_defaults(func=lambda args: fetch(args.remote, all=args.all, set_upstream=args.set_upstream, tags=args.tags))

    return parser