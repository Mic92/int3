import argparse
import os
from pathlib import Path

from .errors import Int3Error

INT3_MACRO = "-DINT3=<int3/__FILE__-__LINE__>"


def find_int3_directory() -> Path:
    p = Path(os.getcwd())
    while True:
        int3_dir = p.joinpath(".int3")
        if int3_dir.exists():
            return int3_dir.resolve()
        if p.parent == p:
            raise Int3Error(".int3 directory not found")
        p = p.parent


def cflags_command(args: argparse.Namespace) -> None:
    int3_dir = find_int3_directory()
    inc_dir = int3_dir.joinpath("includes")
    lib_dir = int3_dir.joinpath("lib")
    t =f"""
-I {inc_dir} {INT3_MACRO} -Wl,-rpath,{lib_dir} -L{lib_dir} -lint3
"""
    print(t.strip())
