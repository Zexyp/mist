import argparse
from ... import Mist

# TODO: -q --quiet, -v --verbose, --progress, --[no-]progress, --[no-]recurse-submodules[=<no-demand>], -n, --[no-]stat,

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("pull")
    parser.add_argument("repository", metavar="<repository>", nargs="?")
    parser.add_argument("--set-upstream", action="store_true")

    def func(args):
        if args.set_upstream:
            assert len(args.remote) == 1
            mist.active_remote_name_set(args.remote[0])

        remotes = args.repository or [mist.active_remote_name_get()]
        dirty = False

        for r in remotes:
            mist.fetch(r)
        for r in remotes:
            if mist.merge(r):
                dirty = True

        if not dirty:
            print("Already up to date.")

    parser.set_defaults(func=func, parser=parser)
    return parser