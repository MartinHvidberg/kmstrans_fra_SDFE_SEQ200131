#!python
import os
import glob
import sys
import subprocess
TRLIB_CLONE_CMD = "hg clone https://bitbucket.org/kms/trlib -r 1.1"
TRLIB_PULL_CMD = "hg pull -r 1.1"
IS_WIN = sys.platform.startswith("win")  # So msvc or mingw - use def file
TRLIB=os.path.abspath("trlib")
#Option format: key, checker, converter, help, default_val
REQUIRED = [("gdal_include", os.path.isdir, os.path.abspath, "Include files for GDAL")] 
opt_gdal_lib = ("gdal_lib", None, None, "Path GDAL (import) library.")
opt_gdal_dir = ("gdal_dir", os.path.isdir, os.path.abspath,"Search path for gdal library")
OPTIONAL = [("debug", None, bool, "Do a debug build?")]
if IS_WIN:
    # Special windows handling - Mingw for now.
    env = Environment(SHLIBPREFIX="lib", ENV=os.environ, tools = ['mingw'])
    REQUIRED.append(opt_gdal_lib)
else:
    env = Environment(SHLIBPREFIX="lib")
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

# Check arguments
if not env.GetOption('clean'):
    for opts, required in ((REQUIRED, True), (OPTIONAL, False)):
       #
        for key, checker, converter, help in opts:
            if (not key in ARGUMENTS):
                    if required:
                        print(help+": "+key+"=<val> required for "+sys.platform)
                        raise ValueError("Option required.")
                    continue
            try:
                val = ARGUMENTS.pop(key)
                if checker:
                    assert checker(val)
                if converter:
                    val = converter(val)
            except Exception as e:
                print("Error parsing opt for: "+key)
                print(help)
                raise e
            else:
                print("Setting "+key+"="+val)
                env[key] = val
            

        
if len(ARGUMENTS)>0:
    print("key=value pairs not consumed: %s" % unicode(ARGUMENTS))
    if not env.GetOption('clean'):
            raise ValueError("Unrecognized argument(s)...")
                
#Make sure that trlib is in place...
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

# Get revision of trlib
if not env.GetOption('clean'):
    get_rev = subprocess.Popen("hg id "+TRLIB, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout,stderr = get_rev.communicate()
    assert get_rev.returncode == 0
    TRLIB_REV_STRING = stdout.strip()
    print("trlib revision: "+TRLIB_REV_STRING)
    env.Append(CPPDEFINES=["TRLIB_REVISION=%s" % TRLIB_REV_STRING])

# Add (absolute path to) header files for trlib
env.Append(CPPPATH = [os.path.join(TRLIB, "TR_INC")])

if env["debug"]:
    env.Append(CCFLAGS = ["-g"])
else:
    env.Append(CCFLAGS = ["-O2"])

# Store some common linking options in env
# Perhaps do something special for windows here



# Build trlib
libtr = env.SConscript("SConscript", variant_dir="buildtr", exports = ["env", "IS_WIN"], duplicate=0)
# Build libtrui
libtrui, trogr = env.SConscript("SOURCE/SConscript", variant_dir="build", exports=["env", "IS_WIN"], duplicate=0)
INSTALL_DIR = "#bin"
# Install TODO: add a real install target which moved python files and binary files
env.Install(INSTALL_DIR, libtr)
env.Install(INSTALL_DIR, libtrui)
env.Install(INSTALL_DIR, trogr)




    
    


