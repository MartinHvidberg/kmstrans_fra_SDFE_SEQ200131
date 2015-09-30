import os
import glob
Import("env","IS_WIN","TRLIB")
# Establish source code
TRLIB_SRC_DIRS=["GEOMETRIC_GEODESY","PHYSICAL_GEODESY","UTILITIES","GENERIC_TRANSFORMATION","SPECIFIC_TRANSFORMATION","METADATA","API","LORD","STRONG"]
DEF_FILE_API=os.path.join(TRLIB,"TR_BUILD","trlib.def")
SRC_TRLIB = []
for folder in TRLIB_SRC_DIRS:
    SRC_TRLIB.extend(glob.glob(os.path.join(TRLIB,"TR_SRC",folder,"*.c")))
if IS_WIN:
    SRC_TRLIB.append(DEF_FILE_API)
print SRC_TRLIB
# BUILD TRLIB
libtr = env.SharedLibrary(target=env["libtr_name"], source=SRC_TRLIB)
Return("libtr")
