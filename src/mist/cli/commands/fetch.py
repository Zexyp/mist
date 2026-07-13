import argparse
import logging
import warnings
from pprint import pformat

from ..completors import RemoteCompleter
from ... import Mist

# TODO: --[no-]all, --negotiate-only, -k --keep, --multiple, -p --prune, -P --prune-tags, -n --no-tags, -t --tags, --[no-]recurse-submodules, -j --jobs, -q --quiet, -v --verbose, --progress, -o --server-option, --[no-]stdin

_DUMP_ENTRIES = False

logger = logging.getLogger(__name__)

def _report_progress(msg):
    raise NotImplementedError
    if msg == "finished":
        print()
        return
    print(f"\r{msg}", end="")

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("fetch", description="Download objects from another repository")
    parser.add_argument("remote", metavar="<remote>", nargs='*').completer = RemoteCompleter(mist)
    parser.add_argument("--tags", action="store_true")
    parser.add_argument("--set-upstream", action="store_true")
    parser.add_argument("--progress", action="store_true") # force progress status, you want it, you will have spaghetti
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--prune", action="store_true")
    parser.add_argument("--prune-tags", action="store_true")

    def func(args):
        if args.set_upstream:
            assert len(args.remote) == 1
            mist.active_remote_name_set(args.remote[0])

        remotes = args.remote or [mist.active_remote_name_get()]
        assert remotes

        progress = _report_progress if args.progress else None

        for r in remotes:
            result = mist.fetch(r, tags=args.tags,
                                progress=progress,
                                dry_run=args.dry_run,
                                force=args.force,
                                prune=args.prune,
                                prune_tags=args.prune_tags)

            if _DUMP_ENTRIES:
                for e in result:
                    logger.debug(e)

    parser.set_defaults(func=func, parser=parser)
    return parser