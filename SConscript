import os
import glob
Import("env","IS_WIN")
cloned_env = env.Clone()
# Establish source code
TRLIB = env["trlib"]
TRLIB_SRC_DIRS=["GEOMETRIC_GEODESY", "PHYSICAL_GEODESY", "UTILITIES",
            "GENERIC_TRANSFORMATION", "SPECIFIC_TRANSFORMATION", "METADATA", 
            "API", "LORD", "STRONG"]
DEF_FILE_API=os.path.join(TRLIB, "TR_BUILD", "trlib.def")
SRC_TRLIB = []
for folder in TRLIB_SRC_DIRS:
    SRC_TRLIB.extend(glob.glob(os.path.join(TRLIB, "TR_SRC", folder, "*.c")))
if IS_WIN:
    SRC_TRLIB.append(DEF_FILE_API)
# Define revision string
cloned_env.Append(CPPDEFINES=["TRLIB_REVISION=%s" % env["TRLIB_REVISION"]])
# BUILD TRLIB
libtr = cloned_env.SharedLibrary(target=env["libtr_name"], source=SRC_TRLIB)
Return("libtr")
