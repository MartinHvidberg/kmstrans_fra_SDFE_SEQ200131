#!python
import os
import sys
import subprocess
TRLIB_CLONE_CMD = "hg clone https://bitbucket.org/kms/trlib -r 1.1"
TRLIB_PULL_CMD = "hg pull -r 1.1"
IS_WIN = sys.platform.startswith("win")  # So msvc or mingw - use def file
TRLIB = os.path.abspath("trlib")
# Option format: key, checker, converter, help
REQUIRED = [("gdal_include", os.path.isdir,
             os.path.abspath, "Include files for GDAL")]
opt_gdal_lib = ("gdal_lib", None, None,
                "Name of gdal library (if non standard).")
opt_gdal_dir = ("gdal_dir", os.path.isdir, os.path.abspath,
                "Search path for gdal library")
OPTIONAL = [("debug", None, int, "Do a debug build?")]
if IS_WIN:
    # Special windows handling - Mingw for now.
    env = Environment(SHLIBPREFIX="lib", ENV=os.environ, tools=['mingw'])
    REQUIRED.append(opt_gdal_lib)
    REQUIRED.append(opt_gdal_dir)
else:
    env = Environment(SHLIBPREFIX="lib")
    OPTIONAL.append(opt_gdal_lib)
    OPTIONAL.append(opt_gdal_dir)
    

# Set defaults
env["trlib"] = TRLIB
env["libtr_name"] = "tr"
env["libtrui_name"] = "trui"
env["trogr_name"] = "trogr"
env["debug"] = 0
env["gdal_lib"] = "gdal"
env["gdal_dir"] = None
env["gdal_include"] = None
env["TRLIB_REVISON"] = "NA"
env["TRUI_REVISION"] = "NA"

# Check arguments
if not env.GetOption('clean'):
    for opts, required in ((REQUIRED, True), (OPTIONAL, False)):
        for key, checker, converter, help in opts:
            if (key not in ARGUMENTS):
                if required:
                    print(help + ": " + key +
                          "=<val> required for " + sys.platform)
                    raise ValueError("Option required.")
                continue
            try:
                val = ARGUMENTS.pop(key)
                if checker:
                    assert checker(val)
                if converter:
                    val = converter(val)
            except Exception as e:
                print("Error parsing val for: " + key + " help: " + help)
                raise e

            else:
                print("Setting " + key + "=" + val)
                env[key] = val


if len(ARGUMENTS) > 0:
    print("key=value pairs not consumed: %s" % unicode(ARGUMENTS))
    if not env.GetOption('clean'):
        raise ValueError("Unrecognized argument(s)...")

# Make sure that trlib is in place...
if not os.path.isdir(TRLIB):
    print(TRLIB_CLONE_CMD)
    rc = subprocess.call(TRLIB_CLONE_CMD, shell=True)
    assert rc == 0
elif not env.GetOption('clean'):
    here = os.getcwd()
    print(TRLIB_PULL_CMD)
    os.chdir(TRLIB)
    rc = subprocess.call(TRLIB_PULL_CMD, shell=True)
    os.chdir(here)
    assert rc == 0


def get_revision(repo):
    get_rev = subprocess.Popen(
        "hg id " + repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = get_rev.communicate()
    assert get_rev.returncode == 0
    rev_string = stdout.strip()
    print("revision of " + repo + ": " + rev_string)
    return rev_string


# Get revisions - very handy for debugging
if not env.GetOption('clean'):
    TRLIB_REVISION = get_revision(TRLIB)
    env["TRLIB_REVISION"] = TRLIB_REVISION
    TRUI_REVISION = get_revision(".")
    env["TRUI_REVISION"] = TRUI_REVISION


# Add (absolute path to) header files for trlib
env.Append(CPPPATH=[os.path.join(TRLIB, "TR_INC")])

if env["debug"]:
    env.Append(CCFLAGS=["-g"])
else:
    env.Append(CCFLAGS=["-O2"])

# Store some common linking options in env
# Perhaps do something special for windows here


# Build trlib
libtr = env.SConscript("SConscript", variant_dir="buildtr",
                       exports=["env", "IS_WIN"], duplicate=0)
# Build libtrui
libtrui, trogr = env.SConscript(
    "SOURCE/SConscript", variant_dir="build", exports=["env", "IS_WIN"], duplicate=0)
INSTALL_DIR = "#bin"
# Install TODO: add a real install target which moved python files and
# binary files
env.Install(INSTALL_DIR, libtr)
env.Install(INSTALL_DIR, libtrui)
env.Install(INSTALL_DIR, trogr)
