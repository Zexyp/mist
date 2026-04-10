import argparse
from typing import Callable
from unittest import case

import mist
from ... import Mist, MistError
from ...config import SimpleConfig


def _choose_cfg_write(mist: Mist, kind: str) -> SimpleConfig:
    match kind:
        case "global":
            return mist.config.general
        case "local" | _:
            if not mist.is_repository():
                raise MistError("--local can only be used inside a mist repository")
            return mist.config.local

def _choose_cfg_read(mist: Mist, kind: str) -> SimpleConfig:
    match kind:
        case "local":
            if not mist.is_repository():
                raise MistError("--local can only be used inside a mist repository")
            return mist.config.local
        case "global":
            return mist.config.general
    return mist.config.active

def _augment_with_types(parser):
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--local", dest="kind", action="store_const", const="local")
    group.add_argument("--global", dest="kind", action="store_const", const="global")
    #group.add_argument("--system", dest="kind", action="store_const", const="system")
    #group.add_argument("--worktree", dest="kind", action="store_const", const="worktree")

def build_parser_list(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("list")
    _augment_with_types(parser)

    def func(args):
        cfg = _choose_cfg_read(mist, args.kind)
        for k, v in cfg.settings.items():
            print(f"{k}={v}")

    parser.set_defaults(func=func, parser=parser)
    return parser

def build_parser_get(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("get")
    _augment_with_types(parser)
    parser.add_argument("name", metavar="<name>")

    def func(args):
        cfg = _choose_cfg_read(mist, args.kind)
        if cfg is None or args.name not in cfg.settings:
            exit(1)
        print(cfg.settings[args.name])

    parser.set_defaults(func=func, parser=parser)
    return parser

def build_parser_set(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("set")
    _augment_with_types(parser)
    parser.add_argument("name", metavar="<name>")
    parser.add_argument("value", metavar="<value>")

    def func(args):
        cfg = _choose_cfg_write(mist, args.kind)
        cfg.set(args.name, args.value)
        cfg.save()

    parser.set_defaults(func=func, parser=parser)
    return parser

def build_parser_unset(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("unset")
    _augment_with_types(parser)
    parser.add_argument("name", metavar="<name>")

    def func(args):
        cfg = _choose_cfg_write(mist, args.kind)
        cfg.unset(args.name)
        cfg.save()

    parser.set_defaults(func=func, parser=parser)
    return parser

def build_parser_edit(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("edit")
    _augment_with_types(parser)

    def func(args):
        raise NotImplementedError

    parser.set_defaults(func=func, parser=parser)
    return parser

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("config")  # locations: global, system, local, worktree?
    parser.set_defaults(parser=parser)

    subparsers_config = parser.add_subparsers()

    build_parser_list(subparsers_config, mist)
    build_parser_get(subparsers_config, mist)
    build_parser_set(subparsers_config, mist)
    build_parser_unset(subparsers_config, mist)
    build_parser_edit(subparsers_config, mist)

    return parser