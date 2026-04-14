import argparse
import warnings

from ... import Mist

# TODO: --[no-]all, --negotiate-only, --dry-run, -k --keep, --multiple, -p --prune, -P --prune-tags, -n --no-tags, -t --tags, --[no-]recurse-submodules, -j --jobs, -q --quiet, -v --verbose, --progress, -o --server-option, --[no-]stdin

def _report_progress(msg):
    if msg == "finished":
        print()
        return
    print(f"\r{msg}", end="")

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("fetch")
    parser.add_argument("remote", metavar="<remote>", nargs='*')
    parser.add_argument("--tags", action="store_true")
    parser.add_argument("--set-upstream", action="store_true")
    parser.add_argument("--progress", action="store_true") # force progress status, you want it, you will have spaghetti

    def func(args):
        if args.set_upstream:
            assert len(args.remote) == 1
            mist.active_remote_set(args.remote[0])

        remotes = args.remote or [mist.active_remote_get()]
        assert remotes

        progress = _report_progress if args.progress else None

        for r in remotes:
            mist.fetch(r, tags=args.tags, progress=progress)

    parser.set_defaults(func=func, parser=parser)
    return parser