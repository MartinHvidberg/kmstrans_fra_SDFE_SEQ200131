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
#Very simplistic build instructions which should work under win, linux and mac as long as gdal is built and findable and gcc or something very similar works....
#Use -cc compiler, e.g. -cc gcc to specify which compiler to use to build trogr.
#should be compatible with tip of trlib repo
import os, sys, shutil
from TrLib_constants import OGRLIB,TRLIB,TROGRNAME

def Usage():
	print("To run:")
	print("%s <path_to_trlib> ..args.." %os.path.basename(sys.argv[0]))
	print("Available arguments (all except -gdal passed on to build script for trlib (if -notrlib is NOT specified)!")
	print("-gdal <path_to_gdal_dev_installation> MUST be specified.")
	print("e.g. -gdal C:\gdal192 or -gdal /opt/local, where these have subdirs 'lib' and 'include'.") 
	print("Use -notrlib to NOT build TrLib, or append extra args to the trlib build script TR_BUILD/py_build.py")
	print("-debug to compile with debug symbols.")
	print("-x64 (Windows only) to use a default 32 to 64bit cross compiler. Alternatively, use -cc")
	print("-cc <gcc_like_compiler> to override the specific compiler 'gcc' in the builds of trogr and trlib.")
	print("OR (optionally) -msvc to build with msvc (cl).")
	print("-bindir <output_dir_for_binaries> (optional) to override the default output dir.")
	print("Use space between option key and option value! e.g. -cc /opt/local/bin/gcc4.6")

if len(sys.argv)<2:
	Usage()
	sys.exit()
args=sys.argv[1:]
trlib=os.path.realpath(args[0])
curdir=os.path.realpath(os.path.dirname(__file__))
outdir=curdir #use this dir as output....	
#Paths
BIN_DIR=os.path.join(outdir,"bin")
SRC_DIR=os.path.join(curdir,"SOURCE")
SRC_LIBREPORT=[os.path.join(SRC_DIR,"Report.c")]
SRC_LIBOGR=[os.path.join(SRC_DIR,"ogrTRogr.c")]
DEF_LIBREPORT=os.path.join(SRC_DIR,"libreport.def")
DEF_LIBOGR=os.path.join(SRC_DIR,"libtrogr.def")
SRC_MAIN=[os.path.join(SRC_DIR,fname) for fname in ["main.c","TransformText.c","TransformDSFL.c","tr_DSFL.c","my_get_opt.c"]]
INC_TRLIB=[os.path.join(trlib,"TR_INC")]
#Import build system
sys.path.insert(0,os.path.join(trlib,"TR_BUILD"))
import core
import cc
import py_build
#Check options
IS_MSVC="-msvc" in args
DEBUG="-debug" in args

if (not "-gdal" in args) or (not (core.IS_WINDOWS) and IS_MSVC):
	Usage()
	sys.exit()

if IS_MSVC:
	if "-x64" in args:
		compiler=cc.msvc64()
	else:
		compiler=cc.msvc32()
else:
	if "-x64" in args:
		compiler=cc.mingw64()
	elif core.IS_WINDOWS:
		compiler=cc.mingw32()
	elif core.IS_MAC:
		compiler=cc.gcc_mac()
	else:
		compiler=cc.gcc_nix()
#arg which should not be removed
if "-cc" in args:
	index=args.index("-cc")+1
	override=args[index]
	compiler.overrideCompiler(override)

#pop this arg and its value...
if "-gdal" in args:
	index=args.index("-gdal")+1
	gdal=os.path.realpath(args.pop(index))
	args.pop(index-1)
	link_gdal=["-L%s" %os.path.join(gdal,"lib"),"-lgdal"]
	gdal_include=os.path.join(gdal,"include")
	gdal_lib=os.path.join(gdal,"lib","gdal_i.lib")
else:
	link_gdal=["-lgdal"]

#pop this arg and its value... Useful e.g. when crosscompiling..
if "-bindir" in args:
	index=args.index("-bindir")+1
	BIN_DIR=args.pop(index)
	args.pop(index-1)
	
#SET OUTPUT NAMES

try:
	os.mkdir(BIN_DIR)
except:
	pass
libogr=os.path.join(BIN_DIR,OGRLIB)
libreport=os.path.join(BIN_DIR,"libreport")+core.DLL
libtr=os.path.join(BIN_DIR,TRLIB) #.DLL already appended
trogr=os.path.join(BIN_DIR,TROGRNAME)+core.EXE #.EXE already appended?
buildtrlib=os.path.join(trlib,"TR_BUILD","py_build.py")
#BUILD C-source#
if not "-notrlib" in args:
	print "Building TrLib"
	py_build_args=["py_build.py"]+[trlib,"-build","-all","-o",libtr]
	if len(args)>1:
		py_build_args+=args[1:]
	ok=py_build.main(py_build_args)
	sys.stdout=sys.__stdout__
	sys.stderr=sys.__stderr__
	print("Build was ok: %s" %(ok==0))
	if (ok!=0):
		sys.exit(1)
	
BUILD_DIR=os.path.realpath(os.path.join(curdir,"BUILD_PY","trogr"))
try:
	os.mkdir(BUILD_DIR)
except:
	pass
#build libreport
ok=core.Build(compiler,libreport,SRC_LIBREPORT,is_debug=DEBUG,link_libraries=compiler.LINK_LIBRARIES,def_file=DEF_LIBREPORT,build_dir=BUILD_DIR,link_all=False)
#build libogr
if (not ok):
	sys.exit(1)
if core.IS_WINDOWS:
	link_libraries=compiler.LINK_LIBRARIES+[gdal_lib,libtr,libreport]
else:
	link_libraries=compiler.LINK_LIBRARIES+link_gdal+[libtr,libreport]

include=INC_TRLIB+[gdal_include]
ok=core.Build(compiler,libogr,SRC_LIBOGR,include,is_debug=DEBUG,link_libraries=link_libraries,def_file=DEF_LIBOGR,build_dir=BUILD_DIR,link_all=False)
#build trogr
if (not ok):
	sys.exit(1)
link_libraries=compiler.LINK_LIBRARIES+[libtr,libreport,libogr]
ok=core.Build(compiler,trogr,SRC_MAIN,include,is_library=False,is_debug=DEBUG,link_libraries=link_libraries,build_dir=BUILD_DIR,link_all=False)
if (not ok):
	sys.exit(1)
try:
	shutil.rmtree("BUILD_PY")
except:
	pass
print("Build succeeded!")
sys.exit(0)









