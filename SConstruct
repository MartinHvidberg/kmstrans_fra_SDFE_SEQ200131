#!python
import os
import glob
import sys
import subprocess
TRLIB_CLONE_CMD = "hg clone https://bitbucket.org/kms/trlib -r 1.1"
TRLIB_PULL_CMD = "hg pull -r 1.1"
IS_WIN = sys.platform.startswith("win")  # So msvc or mingw - use def file
TRLIB=os.path.abspath("trlib")
env = Environment(SHLIBPREFIX="lib")
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

# if not in clean mode add gdal headers from command line
if not env.GetOption('clean'):
    assert "gdal_include" in ARGUMENTS
    gdal_include = ARGUMENTS["gdal_include"]
    assert os.path.isdir(gdal_include)
gdal_include = ARGUMENTS.get("gdal_include",None)
   
if ARGUMENTS.get("debug",0):
    env.Append(CCFLAGS = '-g')

# Store some common linking options in env
# Perhaps do something special for windows here
env["libtr_name"] = "tr"
env["libtrui_name"] = "trui"
env["trogr_name"] = "trogr"
env["gdal_include"] = gdal_include 

# Build trlib
libtr = env.SConscript("SConscript", variant_dir="buildtr", exports = ["env", "IS_WIN", "TRLIB"], duplicate=0)
# Build libtrui
libtrui, trogr = env.SConscript("SOURCE/SConscript", variant_dir="build", exports=["env", "IS_WIN"], duplicate=0)
INSTALL_DIR = "#bin"
# Install TODO: add a real install target which moved python files and binary files
env.Install(INSTALL_DIR, libtr)
env.Install(INSTALL_DIR, libtrui)
env.Install(INSTALL_DIR, trogr)




    
    


