#!/usr/bin/env python
import argparse
import os
import random
import string 

from clang.cindex import CursorKind, Index, TranslationUnit, TypeKind, SourceLocation, Cursor
from typing import List, IO, Tuple
from pathlib import Path

from .errors import Int3Error
from .path import ROOT, get_lib_src, get_int3_dirs


def _escape_c_string(string: str) -> str:
    result = ""
    for c in string:
        if not (32 <= ord(c) < 127) or c == "\\" or c == '"':
            result += "\\%03o" % ord(c)
        else:
            result += c
    return '"' + result + '"'


def _find_callsites(node: Cursor, closure: List[Cursor], in_function: bool) -> Tuple[List[Cursor],List[List[Cursor]]]:
    """
    Macro invocations are not aligned with the remaining ast.
    - We need the macro invocation to get source line, where INT3 was included
    - To get the position in the AST, we look for a our dummy header, this
      gives us the closure with all defined variables and symbols
    We can combine both information with a simple zip(a,b)
    """
    include_locations = []
    closures = []
    # reset closure outside of functions
    if not in_function:
        closure = []
    if node.kind == CursorKind.MACRO_INSTANTIATION and node.spelling == "INT3":
        include_locations.append(node.location)
    elif in_function:
        if (
            node.kind == CursorKind.COMPOUND_STMT
            and node.location is not None
            and node.location.file.name.endswith("int3/dummy.h")
        ):
            closures.append(closure)
        elif node.kind == CursorKind.VAR_DECL or node.kind == CursorKind.PARM_DECL:
            closure.append(node)

    for c in node.get_children():
        in_function = in_function or node.kind == CursorKind.FUNCTION_DECL
        include_locations_, closures_ = _find_callsites(c, closure, in_function)
        include_locations.extend(include_locations_)
        closures.extend(closures_)

    return include_locations, closures


def find_callsites(nodes: Cursor) -> List[Tuple[Cursor,List[Cursor]]]: 
    include_locations, closures = _find_callsites(nodes, [], False)
    return zip(include_locations, closures)


INT3_REPL_PRELUDE = [
    "#define INT3 <int3/dummy.h>",
    # for C mode this needs to be put in `extern "C" {}` block
    '''#include \\"{file}\\"''',
]

INT3_VARIABLES_TEMPLATE = """{type}& {name} = *({type}*) %p;"""

INT3_HEADER_TEMPLATE = """
#pragma once

#if defined(__cplusplus)
extern "C" {{
#endif //__cplusplus

void {function_name}({variables});

#if defined(__cplusplus)
}} // extern "C"
#endif //__cplusplus
"""

INT3_SRC_TEMPLATE = """
#if defined(__cplusplus)
extern "C" {{
#endif //__cplusplus

void {function_name}({variables}) {{
    asm volatile ("int3");
}}

#if defined(__cplusplus)
}} //extern "C"
#endif //__cplusplus
"""

def open_header_file(location: SourceLocation) -> IO[str]:
    file_name = location.file.name
    path = '{}-{}'.format(file_name, location.line)
    header_file = get_int3_dirs()["includes"].joinpath(path)
    header_file.parent.mkdir(parents = True, exist_ok = True)
    return open(header_file, "w+")

def get_types_vars(closure: List[Cursor]) -> List[Tuple[str,str]]:
    res : List[Tuple[str,str]] = []
    for node in closure:
        res.append((node.type.spelling, node.spelling))
    return res


def write_method(f: IO[str], template: str, f_name: str, variables: str) -> None:
    f.write(template.format(function_name = f_name, variables = variables))


def write_src(libsrc_file: IO[str], header_file: IO[str], f_name: str, variables: List[Tuple[str,str]]) -> None:
    var_strlist = []
    for type_name, var_name in variables:
        var_strlist.append("{type} & {variable}".format(type=type_name, variable=var_name))
    var_str = ", ".join(var_strlist)
    write_method(libsrc_file, INT3_SRC_TEMPLATE, f_name, var_str)
    write_method(header_file, INT3_HEADER_TEMPLATE, f_name, var_str)


def generate_unique_funtion_name() -> str:
    return "int3_" + ''.join(random.choices(string.ascii_letters + string.digits, k = 16))


def generate_header_for_file(libsrc_file: IO[str], sourcefile: str) -> None:
    index = Index.create()
    cflags = [
        "-I{include}".format(include=ROOT.joinpath("int3/includes")),
        "-DINT3=<int3/dummy.h>",
    ]
    for flag in os.getenv("NIX_CFLAGS_COMPILE", "").split(" "):
        if len(flag) > 0:
            cflags.append(flag)

    tu = index.parse(
        sourcefile, cflags, options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
    )
    if not tu:
        raise Int3Error("unable to load input")

    callsites = find_callsites(tu.cursor) 
    for (location, closure) in callsites:
        with open_header_file(location) as header_file:
            write_src(libsrc_file, header_file, generate_unique_funtion_name(), get_types_vars(closure))


def prebuild_command(args: argparse.Namespace) -> None:
    with get_lib_src().open(mode="a") as libsrc_file:
        generate_header_for_file(libsrc_file, args.sourcefile)
