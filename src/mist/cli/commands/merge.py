import argparse

from ..cli_utils import summon_subcommand
from ..completors import RemoteCompleter
from ... import Mist

# TODO: -s <strategy> --strategy=<strategy>, -X <option> --strategy-option=<option>, -q --quiet, -v --verbose, --[no-]progress, --allow-unrelated-histories, --abort, --quit, --continue,

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = summon_subcommand(subparsers, "merge", description="Join objects from repositories")
    parser.add_argument("remote", metavar="<remote>", nargs="*").completer = RemoteCompleter(mist)
    action_group = parser.add_mutually_exclusive_group(required=False)
    action_group.add_argument("--continue", action="store_true")
    action_group.add_argument("--abort", action="store_true")
    action_group.add_argument("--quit", action="store_true")

    def func(args):
        remotes = args.remote or [mist.active_remote_name_get()]
        if not mist.merge(remotes):
            print("Already up to date.")

    parser.set_defaults(func=func, parser=parser)
    return parser
