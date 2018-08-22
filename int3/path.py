import os

from pathlib import Path
from typing import Dict

from .errors import Int3Error

ROOT = Path(__file__).parent.parent.resolve()
INT3_DIR = ".int3"

def find_int3_directory() -> Path:
    p = Path(os.getcwd())
    while True:
        int3_dir = p.joinpath(INT3_DIR)
        if int3_dir.exists():
            return int3_dir.resolve()
        if p.parent == p:
            raise Int3Error(".int3 directory not found")
        p = p.parent

def get_int3_dirs() -> Dict[str, Path]:
    int3_dir = find_int3_directory()
    return {
            "includes" : int3_dir.joinpath("includes"),
            "lib"      : int3_dir.joinpath("lib")
            }

def get_lib_src() -> Path:
    lib_dir = get_int3_dirs()["lib"]
    return lib_dir.joinpath("int3.cpp")
