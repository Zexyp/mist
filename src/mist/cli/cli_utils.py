import argparse

from .actions import CommandHelpAction

_ALIGN_TO_MULTIPLE = 8

def pad_align(name: str) -> str:
    return name + " " * (-len(name) % _ALIGN_TO_MULTIPLE)

def summon_subcommand(subparsers, name, **kwargs) -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = subparsers.add_parser(name, add_help=False, **kwargs)
    parser.add_argument("-h", "--help", nargs=0, action=CommandHelpAction)
    return parser

# TODO: add a mechanism to update progress on delay
