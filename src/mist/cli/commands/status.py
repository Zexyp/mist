import argparse
from ... import Mist

def build_parser(subparsers, mist: Mist) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("status")
    parser.set_defaults(func=lambda args: status())
