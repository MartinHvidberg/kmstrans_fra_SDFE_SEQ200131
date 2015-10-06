from distutils.core import setup
import py2exe
import shutil
import os
import sys
import glob
import time
if len(sys.argv)>1:
	oname=sys.argv.pop(1)
else:
	oname="KMSTRANS2"
try:
	shutil.rmtree("dist") #delete previous output
except:
	pass
sys.argv.append("py2exe")
extra_files=["LICENCE.isc","ReadMe.txt"]
BIN=glob.glob(".\\bin\\*")
COAST=glob.glob(".\\coast\\*world*")
TEST_DATA=glob.glob(".\\test_data\\*")
excludes=["Tkconstants","Tkinter","tcl","matplotlib","pylab","numpy","setup","distutils","pywin","pywin.dialogs","pywin.dialogs.list"]
setup(   options = {'py2exe': { 'excludes': excludes, 'includes':['encodings','sip'], "optimize" : 1}},
windows=[{"script" : "Trui.py"}],
data_files=[("",extra_files),("bin",BIN),("coast",COAST),("test_data",TEST_DATA)])
MS_DLLS=glob.glob(".\\dist\\msvcp*.dll") #ms dlls to manually remove afterwards...
MS_DLLS.extend(glob.glob(".\\dist\\API-MS*.dll"))
MS_DLLS.extend([".\\dist\\"+x for x in ["KERNELBASE.dll","MSASN1.dll","CRYPT32.dll"]])
try:
	shutil.copytree("gdal","dist\\gdal")
except:
	print("Could not copy gdal installation")
for name in MS_DLLS:
	try:
		print("Removing "+name)
		os.remove(name)
	except:
		print("Failed...")
try:
	shutil.copytree("doc","dist\\doc")
except:
	print("Could not copy documentation")
#write build info#
os.system("hg identify > .\\dist\\build_info.txt")
f=open(".\\dist\\build_info.txt","a")
f.write("\nBuilt with py2exe on %s\n" %time.asctime())
f.write("Python version:\n%s" %sys.version)
f.close()
os.rename("dist\\Trui.exe","dist\\KMSTrans2.exe")
os.rename("dist",oname)
sys.exit()
