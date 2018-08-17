#!/usr/bin/env python

from setuptools import setup, find_packages
import sys

assert sys.version_info >= (3, 6, 0), "int3 requires Python 3.6+"
setup(
    name="int3",
    version="0.2.0",
    description="Better debugger breakpoints",
    author="Jörg Thalheim",
    author_email="joerg@thalheim.io",
    url="https://github.com/Mic92/int3",
    license="MIT",
    packages=find_packages(),
    package_data={"int3": ["int3/includes/*"]},
    entry_points={"console_scripts": ["int3 = int3:main"]},
    extras_require={"dev": ["mypy", "flake8>=3.5,<3.6", "black"]},
    install_requires=["clang"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
    ],
)
