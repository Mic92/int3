import argparse
import os
from pathlib import Path

from .errors import Int3Error
from .path import find_int3_directory

INT3_MACRO = "-DINT3=<int3/__FILE__-__LINE__>"


def cflags_command(args: argparse.Namespace) -> None:
    int3_dirs = get_int3_dirs()
    inc_dir = int3_dirs["includes"]
    lib_dir = int3_dirs["lib"]
    t =f"""
-I {inc_dir} {INT3_MACRO} -Wl,-rpath,{lib_dir} -L{lib_dir} -lint3
"""
    print(t.strip())
