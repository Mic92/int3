#!/usr/bin/env python
import argparse
import os

from clang.cindex import CursorKind, Index, TranslationUnit, TypeKind

from .errors import Int3Error
from .path import ROOT


def _escape_c_string(string: str) -> str:
    result = ""
    for c in string:
        if not (32 <= ord(c) < 127) or c == "\\" or c == '"':
            result += "\\%03o" % ord(c)
        else:
            result += c
    return '"' + result + '"'


def _find_callsites(node, closure, in_function):
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


def find_callsites(nodes):
    include_locations, closures = _find_callsites(nodes, [], False)
    return zip(include_locations, closures)


INT3_REPL_PRELUDE = [
    "#define INT3 <int3/dummy.h>",
    # for C mode this needs to be put in `extern "C" {}` block
    '''#include \\"{file}\\"''',
]

INT3_VARIABLES_TEMPLATE = """{type}& {name} = *({type}*) %p;"""

INT3_HEADER_TEMPLATE = """
void inspectorRunRepl(const char* path, unsigned lineNumber, const char* clingDeclare, const char* clingContext, ...);
inspectorRunRepl("{file}", {line}, "{declare}", "{prelude}", {pointerlist});
"""


def write_header(location, closure):
    file_name = location.file.name
    # expanded form of  __FILE__ __LINE__
    path = '"{}"-{}'.format(file_name, location.line)
    header_file = os.path.join(".int3-includes", "int3", path)
    os.makedirs(os.path.dirname(header_file), exist_ok=True)
    prelude = []
    pointerlist = []
    for node in closure:
        prelude.append(
            INT3_VARIABLES_TEMPLATE.format(type=node.type.spelling, name=node.spelling)
        )
        pointerlist.append("&{variable}".format(variable=node.spelling))
    with open(header_file, "w+") as f:
        print(header_file)
        data = dict(
            file=file_name,
            line=location.line,
            declare="\\n".join(INT3_REPL_PRELUDE).format(file=file_name),
            prelude="\\n".join(prelude),
            pointerlist=", ".join(pointerlist),
        )
        f.write(INT3_HEADER_TEMPLATE.format(**data))


def generate_header_for_file(sourcefile: str) -> None:
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
        write_header(location, closure)


def prebuild_command(args: argparse.Namespace) -> None:
    generate_header_for_file(args.sourcefile)
