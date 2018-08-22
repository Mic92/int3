#!/usr/bin/env python
import argparse
import os
from pathlib import Path

from .path import get_int3_dirs, INT3_DIR

def init_command(args: argparse.Namespace) -> None:
    os.makedirs(INT3_DIR, exist_ok = True) 
    for key, directory in get_int3_dirs().items():
        directory.mkdir(parents = True, exist_ok = True)
