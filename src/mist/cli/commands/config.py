import argparse
from typing import Callable
from unittest import case

import mist
from ... import Mist, MistError
from ...config import ConfigReader
from ...messages import *

# TODO: add system level
# TODO: rename-section, remove-section
# TODO: --append, --comment, --all, --system, -f --file, --type, -z --null, --name-only, --show-origin, --show-scope, --[no-]includes, --default <value>

def _choose_cfg_write(mist: Mist, kind: str) -> ConfigReader:
    match kind:
        case "global":
            return mist.config.general
        case "local":
            if not mist.is_repository():
                raise MistError(MSG_LOCAL_NO_REPOSITORY)
            return mist.config.local
        case _:
            if not mist.is_repository():
                raise MistError(MSG_NO_CONFIG_TO_WRITE)
            return mist.config.local

def _choose_cfg_read(mist: Mist, kind: str) -> ConfigReader:
    match kind:
        case "local":
            if not mist.is_repository():
                raise MistError(MSG_LOCAL_NO_REPOSITORY)
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

#def _augment_for_read(parser):

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
            parser.exit(1)
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
        editor = mist.config.active.get("core.editor", None)
        assert editor is not None
        cfg = _choose_cfg_write(mist, args.kind)

        import subprocess
        subprocess.call([editor, cfg.path])

    parser.set_defaults(func=func, parser=parser)
    return parser

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("config", description="Get and set repository or global options")  # locations: global, system, local, worktree?
    parser.set_defaults(parser=parser)

    subparsers_config = parser.add_subparsers()

    build_parser_list(subparsers_config, mist)
    build_parser_get(subparsers_config, mist)
    build_parser_set(subparsers_config, mist)
    build_parser_unset(subparsers_config, mist)
    build_parser_edit(subparsers_config, mist)

    return parser