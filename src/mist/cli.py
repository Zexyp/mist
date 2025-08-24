import argparse
import sys

from . import *
from . import shenanigans

def build_parser_remote(subparsers):
    parser = subparsers.add_parser("remote")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.set_defaults(func=lambda args: remote_list(args.verbose))

    subparsers_remote = parser.add_subparsers()

    parser_add = subparsers_remote.add_parser("add")
    parser_add.add_argument("name")
    parser_add.add_argument("url")
    parser_add.set_defaults(func=lambda args: remote_add(args.name, args.url))

    parser_set_url = subparsers_remote.add_parser("set-url")
    parser_set_url.add_argument("name")
    parser_set_url.add_argument("newurl")
    parser_set_url.set_defaults(func=lambda args: remote_set_url(args.name, args.newurl))

    parser_remove = subparsers_remote.add_parser("remove", aliases=["rm"])
    parser_remove.add_argument("name")
    parser_remove.set_defaults(func=lambda args: remote_remove(args.name))

    return parser

def build_parser_fetch(subparsers):
    parser = subparsers.add_parser("fetch")
    parser.add_argument("remote", nargs='?')
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--set-upstream", action="store_true")
    parser.set_defaults(func=lambda args: fetch(args.remote, all=args.all, set_upstream=args.set_upstream))

    return parser

def build_parser_pull(subparsers):
    parser = subparsers.add_parser("pull")
    parser.add_argument("remote", nargs='?')
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--set-upstream", action="store_true")
    parser.set_defaults(func=lambda args: pull(args.remote, all=args.all, set_upstream=args.set_upstream))

    return parser

def build_parser():
    parser = argparse.ArgumentParser()

    from importlib.metadata import version
    parser.add_argument('--version', action='version', version=f"Mist {version(__package__)}")

    subparsers = parser.add_subparsers()

    parser_init = subparsers.add_parser("init")
    parser_init.set_defaults(func=lambda args: init())
    parser_remote = build_parser_remote(subparsers)
    parser_fetch = build_parser_fetch(subparsers)
    parser_status = subparsers.add_parser("status")
    parser_status.set_defaults(func=lambda args: status())
    #parser_merge = subparsers.add_parser("merge")
    #parser_diff = subparsers.add_parser("diff")
    #parser_submodule = subparsers.add_parser("submodule")
    #parser_pull = subparsers.add_parser("pull")
    #parser_pull = subparsers.add_parser("clone")
    #parser_config = subparsers.add_parser("config") # locations: global, system, local, worktree?

    parser_list = subparsers.add_parser("list", aliases=["ls"])
    parser_list.set_defaults(func=lambda args: print("\n".join(shenanigans.get_remote_ids("asd"))))
    parser_entry = subparsers.add_parser("entry")
    parser_entry.add_argument("index")
    def entry(index):
        print(shenanigans.get_remote_ids("asd", start=index + 1, end=index + 1))
    parser_entry.set_defaults(func=lambda args: entry(int(args.index)))

    return parser

def run():
    parser = build_parser()

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

import string
import re

def print_progress_bar(amount: int | float, total: int | float,
                       prefix: str = "",
                       suffix: str = "",
                       decimals: int = 0,
                       percent_decimals: int = 1,
                       width: int | None = None, # automatic if set to None, 0 to force bar length
                       bar_length: int = 80,
                       fill: str = '█',
                       empty: str = '-',
                       template: str ="$prefix |$bar| $percent % ($amount/$total) $suffix",
                       finish: bool | None = None # if set to None finishing action is automatic
                       ):
    """
    this function is not just *stolen*, it's also improved
    it's my precious child
    """
    assert 0 <= amount <= total

    percent_length = 3 + 1 + percent_decimals
    total_string = f"{total:.{decimals}f}"
    total_string_length = len(total_string)

    # auto set width
    if width is None and sys.stdout.isatty():
        width = os.get_terminal_size().columns

    if width:
        # put skull emoji here for the regex
        # default patter from docs https://docs.python.org/3/library/string.html
        junk_length = len(re.sub(r"(?<!\$)\$([_a-z][_a-z0-9]*)|(?<!\$)\$\{([_a-z][_a-z0-9]*)\}", "", template)) + len(prefix) + len(suffix) + percent_length + total_string_length * 2
        # clamp
        bar_length = max(width - junk_length, 0)

    if total:
        percent_value = 100 * (amount / total)
        percent = f"{percent_value:.{percent_decimals}f}".rjust(percent_length)
        filled_length = min(bar_length, int(bar_length * amount // total))
    else:
        percent = "-".rjust(percent_length)
        filled_length = 0

    bar = fill * filled_length + empty * (bar_length - filled_length)

    line = string.Template(template).safe_substitute(prefix=prefix,
                                                     bar=bar,
                                                     percent=percent,
                                                     amount=f"{amount:.{decimals}f}".rjust(total_string_length),
                                                     total=total_string,
                                                     suffix=suffix)
    print(f"\r{line}", end="")

    # print new line on complete
    if amount == total and finish is None:
        print()

    if finish:
        print()

# state of progress
_last_progress_total: int | None = None
_last_print: int = None

# cfg
_progress_update = 1000 # in ms, None - disabled

def progress_start(total):
    """used to initialize progress bar"""
    if _progress_update is None:
        return
    global _last_progress_total
    assert _last_progress_total is None

    _last_progress_total = total
    print_progress_bar(0, _last_progress_total, prefix=f"Preparing...:", finish=False)


def progress_update(iteration):
    """update state"""
    if _progress_update is None:
        return
    global _last_progress_total
    assert _last_progress_total is not None
    if iteration > _last_progress_total:
        _last_progress_total = iteration
    if iteration % _progress_update != 0:
        return
    print_progress_bar(iteration, _last_progress_total, prefix=f"Working... ({str(iteration).rjust(len(str(_last_progress_total)))}/{_last_progress_total}):", finish=False)


def progress_finish():
    """fill progress bar and reset context"""
    if _progress_update is None:
        return
    global _last_progress_total
    assert _last_progress_total is not None
    print_progress_bar(_last_progress_total, _last_progress_total, prefix=f"Done ({_last_progress_total}/{_last_progress_total}):", finish=True)
    _last_progress_total = None
