from distutils.core import setup
import py2exe
import shutil
import os
import sys
import glob
sys.argv.append("py2exe")
extra_files=["icon.png","LICENCE.isc","ReadMe.txt"]
BIN=glob.glob(".\\bin\\*")
COAST=glob.glob(".\\coast\\*world*")
excludes=["Tkconstants","Tkinter","tcl","matplotlib","pylab","javaxx"]
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
os.rename("dist\\Trui.exe","KMSTrans2.exe")
os.rename("dist","KMSTRANS2")
sys.exit()
