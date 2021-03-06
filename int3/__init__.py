import sys
import argparse
from typing import List

from .prebuild import prebuild_command
from .cflags import cflags_command
from .init import init_command


def parse_args(command: str, args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=command)
    subparsers = parser.add_subparsers()

    prebuild_parser = subparsers.add_parser("prebuild")
    prebuild_parser.add_argument("sourcefile")
    prebuild_parser.set_defaults(func=prebuild_command)

    cflags = subparsers.add_parser("cflags")
    cflags.set_defaults(func=cflags_command)

    init = subparsers.add_parser("init")
    init.set_defaults(func=init_command)

    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[0], sys.argv[1:])
    args.func(args)
