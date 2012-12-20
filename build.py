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
import os, sys, shutil
from File2File import OGRLIB
from GSTtrans import LIBNAME,TROGRNAME

def Usage():
	print("To run:")
	print("%s <path_to_trlib> -gdal <path_to_gdal_dev_installation> -cc <gcc_like_compiler> -notrlib OR ...extra args... to py_build.py" %os.path.basename(sys.argv[0]))
	print("-gdal <path_to_gdal_dev_installation> MUST be used ONLY on windows. On Linux set LD_LIBRARY_PATH.")
	print("Use -notrlib to NOT build TrLib, or append extra args to the trlib build script TR_BUILD/py_build.py")
	print("-cc <gcc_like_compiler> to override the specific compiler 'gcc' in the builds of trogr and trlib.")
	print("Use space between option key and option value! e.g. -cc /opt/local/bin/gcc4.6")

def RunCommand(cmd):
	print cmd
	rc=os.system(cmd)
	print("Return code: %d" %rc)
	return rc

if len(sys.argv)<2:
	Usage()
	sys.exit()

args=sys.argv[1:]
trlib=os.path.realpath(args[0])
curdir=os.path.realpath(os.path.dirname(__file__))
outdir=curdir #use this dir as output....	

#arg which should not be removed
if "-cc" in args:
	index=args.index("-cc")+1
	CC=args[index]
else:
	CC="gcc"

IS_WINDOWS=sys.platform.startswith("win")

if (not IS_WINDOWS) and "-gdal" in args:
	Usage()
	sys.exit()

if IS_WINDOWS:
	if not "-gdal" in args:
		Usage()
		sys.exit()
	index=args.index("-gdal")+1
	#pop these two args#
	gdal=os.path.realpath(args.pop(index))
	args.pop(index-1)
	link_gdal="-I%s %s" %(os.path.join(gdal,"include"),os.path.join(gdal,"lib","gdal_i.lib"))
	options=""
	dll=".dll"
	exe=".exe"
elif "darwin" in sys.platform: #MAC
	options="-fPIC"
	dll=".dylib"
	exe=""
	link_gdal="-lgdal"
else: #Linux, or something similar....
	options="-fPIC"
	dll=".so"
	exe=""
	link_gdal="-lgdal"

BIN_DIR=os.path.join(outdir,"bin")
try:
	os.mkdir(BIN_DIR)
except:
	pass
libogr=os.path.join(BIN_DIR,OGRLIB)
libreport=os.path.join(BIN_DIR,"libreport")+dll
libtr=os.path.join(BIN_DIR,LIBNAME)
trogr=os.path.join(BIN_DIR,TROGRNAME)+exe
buildtrlib=os.path.join(trlib,"TR_BUILD","py_build.py")
#BUILD C-source#
if not "-notrlib" in args:
	print "Building TrLib"
	extra_args=""
	if len(args)>1:
		for arg in args[1:]:
			extra_args+=" %s" %arg
	cmd="%s %s -build -all -o %s %s" %(buildtrlib,trlib,libtr,extra_args)
	rc=RunCommand(cmd)
	try:
		shutil.rmtree("BUILD_PY")
	except:
		pass
os.chdir(os.path.join(curdir,"SOURCE"))
print("Building %s..." %TROGRNAME)
cmd="%s -o %s -O2 -shared %s Report.c" %(CC,libreport,options)
rc=RunCommand(cmd)
if not os.path.exists(libtr):
	print("Can't build %s, %s does not exist!" %(TROGRNAME,libtr))
	sys.exit()
cmd="%s -o %s -O2 -shared %s -I%s/TR_INC ogrTRogr.c %s %s %s" %(CC,libogr,options,trlib,link_gdal,libtr,libreport)
rc=RunCommand(cmd)
cmd="%s -o %s -O2  -I%s/TR_INC/ %s TransformDSFL.c main.c TransformText.c %s %s %s" %(CC,trogr,trlib,libtr,link_gdal,libreport,libogr)
rc=RunCommand(cmd)








