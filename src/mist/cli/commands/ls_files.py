import argparse
import os
import warnings

from .. import cli_utils
from ..cli_utils import summon_subcommand
from ... import Mist, ListItemFlag
from ...metadata.worktree import worktree_load


# TODO: --full-name, --[no-]recursive-submodules, --[no-]duplicate

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = summon_subcommand(subparsers, "ls-files")
    parser.add_argument("--verbose", action='store_true', default=None)
    parser.add_argument("-c", "--cached", action='store_true', default=None)
    parser.add_argument("-d", "--deleted", action='store_true', default=None)
    parser.add_argument("-m", "--modified", action='store_true', default=None)
    parser.add_argument("-o", "--others", action='store_true', default=None)
    parser.add_argument("-i", "--ignored", action='store_true', default=None)
    parser.add_argument("-u", "--unmerged", action='store_true', default=None)

    def func(args):
        verbose = args.verbose if args.verbose is not None else mist.config.active.getbool("ls-files.verbose", False)
        cached = args.cached if args.cached is not None else not any([args.cached, args.deleted, args.modified, args.others, args.ignored, args.unmerged])
        debug = mist.config.active.getbool("core.debug", False)

        if args.ignored or args.unmerged:
            raise NotImplementedError

        wt_ents = worktree_load(mist.worktree_dir)
        for e in mist.list_files(
            cached=cached,
            deleted=args.deleted,
            modified=args.modified,
            others=args.others
        ):
            FLAG_LABELS = {
                ListItemFlag.CACHED: "c",
                ListItemFlag.DELETED: "d",
                ListItemFlag.MODIFIED: "m",
                ListItemFlag.OTHERS: "o",
            }

            line = e[1]
            if verbose:
                if e[2] & ListItemFlag.OTHERS:
                    wtis = [we for we in wt_ents if we.id == e[1]]
                    assert len(wtis) == 1
                    line = wtis[0].file
                elif e[2] & ListItemFlag.MODIFIED and debug:
                    wtis = [we for we in wt_ents if we.id == e[1]]
                    assert len(wtis) == 1
                    title = mist.storage.get_object(e[0], e[1]).title
                    line = f"{cli_utils.pad_align(f"{line} ")}{title} => {wtis[0].title}"
                else:
                    title = mist.storage.get_object(e[0], e[1]).title
                    line = f"{cli_utils.pad_align(f"{line} ")}{mist.storage.get_object(e[0], e[1]).title}"

            if debug:
                line = f"{cli_utils.pad_align(f"{"".join(l for f, l in FLAG_LABELS.items() if e[2] & f)} ")}{line}"
            print(line)

    parser.set_defaults(func=func, parser=parser)

    return parser