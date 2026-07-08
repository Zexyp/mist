import argparse
import os

from ... import Mist, MistError, log
from .. import cli_utils

# TODO: -q --quiet, --[no-]sort, -o --[no-]server-option <server-specific>

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("ls-remote")
    parser.add_argument("repository", metavar="<repository>", nargs="?")
    parser.add_argument("-q", "--quiet", action="store_true")

    def func(args):
        url = None
        if args.repository is not None:
            if (args.repository.startswith("https://") or args.repository.startswith("http://")):
                url = args.repository
            elif args.repository and (remote := mist.get_remote(args.repository)):
                url = remote.url
        else:
            remote_name = mist.active_remote_name_get()
            if not remote_name:
                log.fatal("No remote configured to list from.")
                parser.exit(1)

            remote = mist.get_remote(remote_name)
            if remote:
                url = remote.url

        if url is None:
            log.fatal(f"'{args.repository}' does not appear to be a mist repository")
            log.fatal(
                "Could not read from remote repository.\n\nPlease make sure you have the correct access rights\nand the repository exists.")
            parser.exit(1)

        if not args.repository and not args.quiet:
            print(f"From {url}")

        for e in mist.list_remote(url):
            print(f"{cli_utils.pad_align(f"{e.id} ")}{e.title}")

    parser.set_defaults(func=func, parser=parser)

    return parser
