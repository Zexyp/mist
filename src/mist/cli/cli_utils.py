import argparse
import os
import re
import sys

_ALIGN_TO_MULTIPLE = 8

def pad_align(name: str) -> str:
    return name + " " * (-len(name) % _ALIGN_TO_MULTIPLE)

# TODO: add a mechanism to update progress on delay

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=80, width=None, fill='█', empty='-', format='{prefix} |{bar}| {percentage}% {suffix}', finish=None):
    """it's not just stolen, i also modified and improved this"""
    percentage_length = 3 + 1 + decimals

    if width is None and sys.stdout.isatty():
        width = os.get_terminal_size().columns
    if width:
        junk_length = len(re.sub(r'\{.*?\}', '', format)) + len(prefix) + len(suffix) + percentage_length
        length = max(width - junk_length, 0)

    if total:
        percentage_value = 100 * (iteration / float(total))
        percentage = f"{percentage_value:.{decimals}f}".rjust(percentage_length)
        filled_length = min(length, int(length * iteration // total))
    else:
        percentage = "-".rjust(percentage_length)
        filled_length = 0

    bar = fill * filled_length + empty * (length - filled_length)

    line = format.format(prefix=prefix, bar=bar, percentage=percentage, suffix=suffix)
    print(f"\r{line}", end="") # move \r to line if windows fuckery is encountered and end with \r

    # print new line on complete
    if iteration == total and finish is None:
        print()

    if finish:
        print()

def multiline_progress_bar(iteration, total, status, **kwargs):
    sys.stdout.write(
        "\033[2K\r" # clear line
        f"{status}\n"
        "\033[2K\r" # clear line
    )
    print_progress_bar(iteration=iteration, total=total, **kwargs)
    sys.stdout.write("\033[1A\r")
    sys.stdout.flush()

    if "finish" in kwargs and kwargs["finish"]:
        print()

if __name__ == "__main__":
    _test_funcs = [
        print_progress_bar,
        multiline_progress_bar,
    ]

    for f in _test_funcs:
        for i in range(10):
            f(i, 10, "yeet")
            import time

            time.sleep(0.5)
        f(i, 10, "yeet", finish=True)

from .actions import CommandHelpAction

def summon_subcommand(subparsers, name, **kwargs) -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = subparsers.add_parser(name, add_help=False, **kwargs)
    parser.add_argument("-h", "--help", nargs=0, action=CommandHelpAction)
    return parser