import argparse
from ... import Mist

# TODO: -q --quiet, -v --verbose, --progress, --server-option, -n --no-checkout, -c --config <key>=<value>, --no-tags, --recurse-submodules?, -j --jobs

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("clone", description="Clone a repository into a new directory")
    parser.add_argument("url", metavar="<url>")
    parser.add_argument("dir", metavar="<dir>", nargs='?')
    parser.add_argument("-o", "--origin", metavar="<name>")

    def func(args):
        mist.clone(args.url, destination_dir=args.dir, origin=args.origin)

    parser.set_defaults(func=func, parser=parser)
    return parser