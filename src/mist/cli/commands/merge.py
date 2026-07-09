import argparse

from ..completors import RemoteCompleter
from ... import Mist

# TODO: -s <strategy> --strategy=<strategy>, -X <option> --strategy-option=<option>, -q --quiet, -v --verbose, --[no-]progress, --allow-unrelated-histories, --abort, --quit, --continue,

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("merge", description="Join objects from two or more repositories")
    parser.add_argument("remote", metavar="<remote>", nargs="?").completer = RemoteCompleter(mist)

    def func(args):
        remote = args.remote or mist.active_remote_name_get()
        if not mist.merge(remote):
            print("Already up to date.")

    parser.set_defaults(func=func, parser=parser)
    return parser