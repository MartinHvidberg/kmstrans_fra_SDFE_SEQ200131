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
excludes=["Tkconstants","Tkinter","tcl","matplotlib","pylab","javaxx","numpy"]
setup(   options = {'py2exe': {'excludes': excludes, 'includes':['encodings','sip']}},
windows=[{"script" : "Trui.py"}],
data_files=[("",extra_files),("bin",BIN),("coast",COAST),])
MSVCP=glob.glob(".\\dist\\msvcp*.dll")
try:
	shutil.copytree("gdal","dist\\gdal")
except:
	print("Could not copy gdal installation")
try:
        os.remove(MSVCP[0])
except:
        pass
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
