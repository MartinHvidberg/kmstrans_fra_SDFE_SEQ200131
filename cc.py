# Original work Copyright (c) 2015, Danish Geodata Agency, Denmark
# (Geodatastyrelsen), gst@gst.dk
# Modified work Copyright (c) 2015, Simon Kokkendorff, <silyko at gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

# A single file version of previous python based -
# c build systems developed at the Danish Geodata Agency

"""
Simplistic wrapper of some well known compilers and linkers (primarily gcc, msvc).
Simply build some c source files and link resulting object files to a shared libary or an executable.
Avoids having to maintain several platform specific build systems like make or nmake.
"""



import sys
import os
import subprocess
import glob


# Test for platform

IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = "darwin" in sys.platform
# else we're linux or unix, probably

ALL_OBJ = [".o", ".obj"]  # object files to remove on clean

# Set the extension of shared libraries and executables
if IS_WINDOWS:
    DLL = ".dll"
    EXE = ".exe"
elif IS_MAC:
    DLL = ".dylib"
    EXE = ""
else:
    DLL = ".so"
    EXE = ""


def run_cmd(cmd, echo=True):
    """
    Input a command 'sequence' a list of strings.
    """
    cmd_str = ""
    new_cmd = []
    for item in cmd:
        item = item.strip()
        if item:
            new_cmd.append(item)
            cmd_str += item+" "
    print("%s\n" % cmd_str)
    # this peculiar os specific combination seems to give the desired behaviour
    if IS_WINDOWS:
        proc = subprocess.Popen(new_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
    else:
        proc = subprocess.Popen(cmd_str, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    out = ""
    while proc.poll() is None:
        line = proc.stdout.readline()
        if line.strip() > 0:
            if echo:
                print(line)
            out += line
    # read remaining stuff if any...
    out += proc.stdout.read()
    return proc.returncode, out


class Ccompiler(object):
    """
    Base compiler/linker class, which will be overridden by specific compiler types.
    """
    COMPILER = ""
    LINKER = ""
    IS_MSVC = False
    COMPILE_LIBRARY_RELEASE = []
    COMPILE_LIBRARY_DEBUG = []
    COMPILE_EXE_RELEASE = []
    COMPILE_EXE_DEBUG = []
    LINK_LIBRARY_RELEASE = []
    LINK_LIBRARY_DEBUG = []
    LINK_EXE_RELEASE = []
    LINK_EXE_DEBUG = []
    DEFINE_SWITCH = ""
    INCLUDE_SWITCH = ""
    IMPLIB_EXT = ""
    LINK_OUTPUT_SWITCH = ""
    LINK_LIBRARIES = ""
    VERSION_SWITCH = ""
    DEF_FILE_SWITCH = ""
    IMPLIB_SWITCH = ""
    OBJ_EXTENSION = ""

    def override_compiler(self, cc, linker=None):
        """
        Override the compiler (and possibly the linker) command.
        Useful to select a specific subvariant of compiler (macports, clang, etc.)
        """
        self.COMPILER = cc
        if linker is None:
            self.LINKER = cc
        else:
            self.LINKER = linker

    def get_options(self, is_library=True, is_debug=False):
        if is_library:
            if is_debug:
                return self.COMPILE_LIBRARY_DEBUG, self.LINK_LIBRARY_DEBUG
            else:
                return self.COMPILE_LIBRARY_RELEASE, self.LINK_LIBRARY_RELEASE
        else:
            if is_debug:
                return self.COMPILE_EXE_DEBUG, self.LINK_EXE_DEBUG
            else:
                return self.COMPILE_EXE_RELEASE, self.LINK_EXE_RELEASE

    def link_output(self, outname):
        # works for everything but MAC gcc!
        return [self.LINK_OUTPUT_SWITCH + outname]

    def get_version(self):
        """Simply fetch the compilers version string"""
        rc, ver = run_cmd([self.COMPILER, self.VERSION_SWITCH])
        if rc == 0:
            return ver.splitlines()[0]
        else:
            return "error"

    def build(self, outname, source, include=None, define=None, is_debug=False, is_library=True, link_libraries=None, def_file="", build_dir=".", link_all=True):
        """
        Build the source - builds outname as a shared library or an executable
        """
        cwd = os.getcwd()

        if not isinstance(self, Ccompiler):
            raise ValueError("Compiler must be a subclass of Ccompiler")

        # normalise paths - if not given as absolute paths...

        includes = map(lambda x: self.INCLUDE_SWITCH + os.path.realpath(x), include) if include else []
        defines = map(lambda x: self.DEFINE_SWITCH + x, define) if define else []
        source = map(os.path.realpath, source)
        # do not normalise link_libraries as it might contains a lot of 'non-path stuff' -
        # use absolute paths here if you must - link_libraries=map(os.path.realpath,link_libraries)
        if len(def_file) > 0:
            def_file = os.path.realpath(def_file)
        outname = os.path.realpath(outname)
        # end normalise paths
        # change path to build dir
        build_dir = os.path.realpath(build_dir)
        if not os.path.exists(build_dir):
            os.makedirs(build_dir)
        os.chdir(build_dir)
        # fetch compile and link options...
        compile_options, link_options = self.get_options(is_library, is_debug)
        do_compile = [self.COMPILER]+defines+compile_options+includes+source
        # import-library and def-file....
        if IS_WINDOWS and is_library:
            if len(def_file) > 0:
                def_file = self.DEF_FILE_SWITCH+def_file
            if self.IS_MSVC:
                implib = self.IMPLIB_SWITCH + os.path.splitext(outname)[0] + self.IMPLIB_EXT
            else:
                implib = ""
        else:
            implib = ""
            def_file = ""

        outname = self.link_output(outname)
        # link all obj-files - perhaps use option to only link those just made? - depends on how builddir is used...
        if link_all:
            obj_files = ["*"+self.OBJ_EXTENSION]
        else:
            obj_files = [os.path.splitext(os.path.basename(fname))[0] + self.OBJ_EXTENSION for fname in source]
        if self.IS_MSVC:
            link_libraries = map(lambda x: x.replace(".dll", ".lib"), link_libraries)
            link = [self.LINKER] + link_options + outname + [implib, def_file] + link_libraries + obj_files
        else:
            link = [self.LINKER] + link_options + outname + [implib] + obj_files + link_libraries + self.LINK_LIBRARIES + [def_file]  # TODO - do something for MSVC also...
        if len(source) > 0:
            rc, text = run_cmd(do_compile)
        else:  # No modified files, I s'pose :-)
            print("No (modified?) source files... linking...")
            rc = 0
        if rc == 0:
            rc, text = run_cmd(link)
        os.chdir(cwd)
        if rc != 0:
            return False
        return True


class Sunc(Ccompiler):
    """
    Sunc compiler - just using the cc command to compile and link.
    """
    COMPILER = "cc"
    LINKER = "cc"
    ALL_BUILD = ["-c"]
    COMPILE_LIBRARY_RELEASE = ALL_BUILD + ["-O3", "-fpic"]
    COMPILE_LIBRARY_DEBUG = ALL_BUILD + ["-g", "-O1", "-fpic"]
    COMPILE_EXE_RELEASE = ALL_BUILD + ["-O3"]
    COMPILE_EXE_DEBUG = ALL_BUILD + ["-g", "-O1"]
    LINK_LIBRARY_RELEASE = ["-shared"]
    LINK_LIBRARY_DEBUG = ["-shared"]
    LINK_EXE_RELEASE = []
    LINK_EXE_DEBUG = []
    LINK_LIBRARIES = ["-lm"]
    DEFINE_SWITCH = "-D"
    INCLUDE_SWITCH = "-I"
    LINK_OUTPUT_SWITCH = "-o"
    OBJ_EXTENSION = ".o"


class Sunc32(Sunc):
    pass


class Sunc64(Sunc):
    ALL_BUILD = Sunc.ALL_BUILD + ["-m64"]


# core gcc class
class Gcc(Ccompiler):
    """
    gcc compiler / linker base class
    """
    COMPILER = "gcc"
    LINKER = "gcc"
    ALL_BUILD = ["-c", "-W", "-Wall", "-Wextra", "-Wno-long-long", "-pedantic"]
    COMPILE_LIBRARY_RELEASE = ALL_BUILD + ["-O3"]
    COMPILE_LIBRARY_DEBUG = ALL_BUILD + ["-g", "-O"]
    COMPILE_EXE_RELEASE = ALL_BUILD + ["-O3"]
    COMPILE_EXE_DEBUG = ALL_BUILD + ["-g", "-O"]
    LINK_LIBRARY_RELEASE = ["-shared"]
    LINK_LIBRARY_DEBUG = ["-shared"]
    LINK_EXE_RELEASE = []
    LINK_EXE_DEBUG = []
    DEFINE_SWITCH = "-D"
    INCLUDE_SWITCH = "-I"
    IMPLIB_EXT = ".a"
    LINK_OUTPUT_SWITCH = "-o"
    LINK_LIBRARIES = []
    DEF_FILE_SWITCH = ""
    IMPLIB_SWITCH = ""
    OBJ_EXTENSION = ".o"


# gcc subvariants
class Mingw32(Gcc):
    LINK_LIBRARY_RELEASE = Gcc.LINK_LIBRARY_RELEASE + ["-Wl,--kill-at"]
    LINK_LIBRARY_DEBUG = Gcc.LINK_LIBRARY_DEBUG + ["-Wl,--kill-at"]
    LINK_LIBRARIES = ["-lkernel32", "-luser32", "-lgdi32", "-lwinspool", "-lshell32", "-lole32", "-loleaut32", "-luuid", "-lcomdlg32", "-ladvapi32"]


class GccNix(Gcc):
    COMPILE_LIBRARY_RELEASE = Gcc.COMPILE_LIBRARY_RELEASE + ["-fPIC"]
    COMPILE_LIBRARY_DEBUG = Gcc.COMPILE_LIBRARY_DEBUG + ["-fPIC"]
    LINK_LIBRARIES = ["-lm"]


class Mingw64(Mingw32):
    COMPILER = "x86_64-w64-mingw32-gcc.exe"
    LINKER = "x86_64-w64-mingw32-gcc.exe"
    LINK_LIBRARIES = []  # TODO - add relevant 64 bit version


class MacportsGcc(GccNix):
    # probably don't use this...
    COMPILER = "/opt/local/bin/gcc-mp-4.6"
    LINKER = "/opt/local/bin/gcc-mp-4.6"


class GccMac(GccNix):

    def link_output(self, outname):
        # we'll need to override this for mac / clang
        return [self.LINK_OUTPUT_SWITCH, outname]


class Msvc(Ccompiler):
    COMPILER = "cl"
    LINKER = "link"
    IS_MSVC = True
    ALL_BUILD = ["/c", "/D_WINDOWS", "/W3", "/Zm1000", "/TC", "/fp:precise", "/D_CRT_SECURE_NO_WARNINGS"]
    COMPILE_LIBRARY_RELEASE = ALL_BUILD + ["/MD", "/O2", "/Ob2", "/DNDEBUG"]
    COMPILE_LIBRARY_DEBUG = ALL_BUILD + ["/D_DEBUG", "/MDd", "/Zi", "/Ob0", "/Od", "/RTC1"]
    # USE SAME RUNTIME FOR EXE PROGRAMS...
    # WILL NOT WANT TO CROSS RUNTIME BOUNDARIES WITH STUFF LIKE FILE POINTERS
    COMPILE_EXE_RELEASE = COMPILE_LIBRARY_RELEASE
    COMPILE_EXE_DEBUG = COMPILE_LIBRARY_DEBUG
    LINK_LIBRARY_RELEASE = ["/DLL", "/INCREMENTAL:NO"]
    LINK_LIBRARY_DEBUG = ["/DLL", "/debug", "/INCREMENTAL"]
    LINK_EXE_RELEASE = ["/INCREMENTAL:NO"]
    LINK_EXE_DEBUG = ["/debug", "/INCREMENTAL"]
    LINK_OUTPUT_SWITCH = "/out:"
    EXE_OUTPUT_SWITCH = "/Fe"
    DEFINE_SWITCH = "/D"
    INCLUDE_SWITCH = "/I"
    VERSION_SWITCH = ""
    DEF_FILE_SWITCH = "/def:"
    IMPLIB_SWITCH = "/implib:"
    IMPLIB_EXT = ".lib"
    OBJ_EXTENSION = ".obj"
    # STANDARD BUILD OPTIONS
    LINK_LIBRARIES = []


class Msvc32(Msvc):
    """msvc subclass which just links some specific win32 libraries"""
    LINK_LIBRARIES = [
        "kernel32.lib", "user32.lib", "gdi32.lib",
        "winspool.lib", "shell32.lib", "ole32.lib", "oleaut32.lib",
        "uuid.lib", "comdlg32.lib", "advapi32.lib"]


class Msvc64(Msvc):
    LINK_LIBRARIES = []  # TODO: add relevant 64bit libraries....

# Various utils below here


def clean(folder):
    print("Cleaning...")
    files = []
    for ext in ALL_OBJ:
        files.extend(glob.glob(os.path.join(folder, "*" + ext)))
    for fname in files:
        os.remove(fname)

# Argparse style attributtes which can be used to validate args in a calling script.
COMPILER_SELECTION_OPTS = {
    "-msvc": {"help": "Use MSVC compiler (windows only).", "action": "store_true"},
    "-sunc": {"help": "Use sun c compiler", "action": "store_true"},
    "-x64": {"help": "Compile 64 bit binaries", "action": "store_true"},
    "-cc": {"help": "Override default compiler command - e.g. 'gcc' - for example to use a 'gcc-like' cross compiler."},
    "-cop": {"help": "Comma separated list of extra options passed on to build (object file compilation only)."}
}


def select_compiler(args):
    # A calling method can validate args using the COMPILER_SELECTION_OPTS above
    compiler = None
    is_64 = "-x64" in args
    if "-msvc" in args:
        if is_64:
            compiler = Msvc64()
        else:
            compiler = Msvc32()
    elif "-sunc" in args:
        if is_64:
            compiler = Sunc64()
        else:
            compiler = Sunc32()
    else:  # defaults
        if IS_WINDOWS:
            if is_64:
                compiler = Mingw64()
            else:
                compiler = Mingw32()
        elif IS_MAC:
            compiler = GccMac()
        else:
            compiler = GccNix()
    if "-cc" in args:
        override = args[args.index("-cc")+1]
        compiler.override_compiler(override)
    # add extra compiler options
    if "-cop" in args:
        compiler.ALL_BUILD += args[args.index("-cop")].split(",")
    return compiler


def is_newer(p1, p2):
    if not os.path.exists(p1):
        return False
    if not os.path.exists(p2):
        return True
    return os.path.getmtime(p1) > os.path.getmtime(p2)


class BuildObject(object):

    """
    A utility class to keep track of source and header files and determine whether this source needs a rebuild.
    """

    def __init__(self, name, outdir, source, include=None, defines=None, link=None, def_file="", is_library=True):
        self.name = name
        self.source = source
        self.include = include
        self.defines = defines
        self.link = link  # a list of other build objects...
        self.def_file = def_file
        self.is_library = is_library  # else exe
        self.needs_rebuild = False
        if is_library:
            self.extension = DLL
        else:
            self.extension = EXE
        self.outname = os.path.join(outdir, self.name) + self.extension

    def set_needs_rebuild(self, dep_files=None):
        # just set this var in the dependency order of mutually dependent builds...
        self.needs_rebuild = False
        files_to_check = self.source + [self.def_file]
        if dep_files is not None:
            files_to_check.extend(dep_files)
        for sname in files_to_check:
            if is_newer(sname, self.outname):
                self.needs_rebuild = True
                return True
        for bobj in self.link:
            if isinstance(bobj, BuildObject) and bobj.needs_rebuild:
                self.needs_rebuild = True
                return True
        return False

    def build(self, compiler, build_dir, is_debug=False):
        if self.link:
            link = [x.outname for x in self.link]
        else:
            link = []
        return compiler.build(self.outname,
                              self.source, self.include, self.defines,
                              is_debug, self.is_library,
                              link, self.def_file,
                              build_dir=build_dir,
                              link_all=False)
