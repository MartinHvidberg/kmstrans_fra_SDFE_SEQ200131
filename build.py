#!/usr/bin/python
"""/*
* Copyright (c) 2012, National Survey and Cadastre, Denmark
* (Kort- og Matrikelstyrelsen), kms@kms.dk
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 */
 """
# Very simplistic build instructions which should work under win, linux and mac as long as gdal is built and findable and gcc or something very similar works....
# Use -cc compiler, e.g. -cc gcc to specify which compiler to use to build trogr.
# should be compatible with trlib version 1.1
import os
import sys
import shutil
import argparse
import cc
from TrLib_constants import LIBTRUI, TRLIB, TROGRNAME

parser = argparse.ArgumentParser(
    description="Simple build script for trui / kmstrans")
parser.add_argument(
    "trlib", help="Path to trlib repo - to build trlib and find header files.")
parser.add_argument("gdal_include", help="Path to gdal header files.")
gr_gdal = parser.add_mutually_exclusive_group()
gr_gdal.add_argument(
    "-gdallib", help="Explicit path to  gdallib to link to (e.g. gdal_i.lib linker stub library on windows for MSVC).")
gr_gdal.add_argument(
    "-gdaldir", help="Tell the build script where to look for the gdal library.")
parser.add_argument("-lgdal",help="Explicit gdal-library name to link to (linux style).", default="gdal")
parser.add_argument("-debug", action="store_true", help="Do debug builds.")
parser.add_argument("-notrlib", action="store_true",
                    help="Do not build trlib (assuming this has already been done).")
for key in cc.COMPILER_SELECTION_OPTS:
    parser.add_argument(key, **cc.COMPILER_SELECTION_OPTS[key])

pargs = parser.parse_args()
here = os.getcwd()
curdir = os.path.realpath(os.path.dirname(__file__))
outdir = curdir  # use this dir as output....

# Paths
trlib = pargs.trlib
BIN_DIR = os.path.join(outdir, "bin")
SRC_DIR = os.path.join(curdir, "SOURCE")
SRC_LIBTRUI = [os.path.join(SRC_DIR, fname) for fname in (
    "ogrTRogr.c", "Report.c", "TransformText.c", "TransformDSFL.c", "tr_DSFL.c", "affine.c")]
DEF_LIBTRUI = os.path.join(SRC_DIR, "libtrui.def")
SRC_MAIN = [os.path.join(SRC_DIR, fname)
            for fname in ["main.c", "my_get_opt.c"]]
INC_TRLIB = [os.path.join(trlib, "TR_INC")]
# Import build system

# Check options
IS_MSVC = pargs.msvc
DEBUG = pargs.debug

if not os.path.exists(BIN_DIR):
    os.mkdir(BIN_DIR)
# output names
libtrui = os.path.join(BIN_DIR, LIBTRUI)
libtr = os.path.join(BIN_DIR, TRLIB)  # .DLL already appended
trogr = os.path.join(BIN_DIR, TROGRNAME) + cc.EXE  # .EXE already appended?

# BUILD C-source#
if not pargs.notrlib:
    print("Building trlib")
    os.chdir(trlib)
    rc, out = cc.run_cmd(["hg", "up", "1.1"])
    assert(rc == 0)
    os.chdir(here)
    py_build = os.path.join(pargs.trlib, "TR_BUILD", "py_build.py")
    py_build_cmd = [sys.executable, py_build,
                    trlib, "-build", "-all", "-o", libtr]
    if pargs.msvc:
        py_build_cmd.append("-msvc")
    if pargs.cc is not None:
        py_build_cmd.extend(["-cc", pargs.cc])
    rc, out = cc.run_cmd(py_build_cmd)
    print("Build was ok: %s" % (rc == 0))
    if (rc != 0):
        sys.exit(1)


if IS_MSVC and parg.gdallib is None:
    raise ValueError("Please specify path to gdal_i.lib for msvc.")

if pargs.gdallib is not None:
        link_gdal = [pargs.gdallib]  # ok so if we're MSVC we en up here...
else:
    link_gdal = ["-l"+pargs.lgdal]
    if pargs.gdaldir is not None:
        link_gdal.append("-L" + pargs.gdaldir)

BUILD_DIR = os.path.realpath(os.path.join(curdir, "BUILD_PY", "trogr"))
if not os.path.exists(BUILD_DIR):
    os.makedirs(BUILD_DIR)

# select the compiler
# some of the ARGS are not compiler selection args, but can be safely
# passed on to select_compiler which only checks for the relevant ones...
compiler = cc.select_compiler(sys.argv[1:])


# build libtrui
link_libraries = link_gdal + [libtr]
include = INC_TRLIB + [pargs.gdal_include]
ok = compiler.build(libtrui, SRC_LIBTRUI, include, is_debug=DEBUG,
              link_libraries=link_libraries, def_file=DEF_LIBTRUI, build_dir=BUILD_DIR, link_all=False)
# build trogr
if (not ok):
    print("Build failed!")
    sys.exit(1)

link_libraries = [libtr, libtrui]

ok = compiler.build(trogr, SRC_MAIN, include, is_library=False, is_debug=DEBUG,
              link_libraries=link_libraries, build_dir=BUILD_DIR, link_all=False)

if (not ok):
    print("Build failed!")
    sys.exit(1)

try:
    shutil.rmtree("BUILD_PY")
except Exception as e:
    pass

print("++++++++++++++++\nBuild succeeded!\n++++++++++++++++")
sys.exit(0)
