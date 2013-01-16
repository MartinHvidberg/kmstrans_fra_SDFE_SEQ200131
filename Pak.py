from distutils.core import setup
import py2exe
import shutil
import os
import sys
import glob
sys.argv.append("py2exe")
mfcdir=sys.prefix+"\\Lib\\site-packages\\pythonwin"
mfc_files= [os.path.join(mfcdir, i) for i in ["mfc90.dll" ,"mfc90u.dll" ,"mfcm90.dll" ,"mfcm90u.dll" ,"Microsoft.VC90.MFC.manifest"]]
crt_files=glob.glob(".\\crt\\*")
extra_files=["icon.png"]
#extra_files+=["C:\\gdal1.9\\bin\\gdal19.dll","C:\\gdal1.9\\bin\\libcurl.dll","C:\\gdal1.9\\bin\\sqlite3.dll",
#GEOIDS=glob.glob("C:\\Geoider\\*")
BIN=glob.glob(".\\bin\\*")
#GDAL=glob.glob(".\\gdal\\*")
#GDAL_DATA=glob.glob(".\\gdal-data\\*")
COAST=glob.glob(".\\coast\\*world*")
DOC=glob.glob(".\\doc\\*")

#Husk pythonw.exe.manifest!!! -not needed in python2.6
excludes=["Tkconstants","Tkinter","tcl","matplotlib","pylab","javaxx"]
setup(   options = {'py2exe': {'excludes': excludes, 'includes':['encodings','sip','win32process','numpy']}},
windows=[{"script" : "GSTtrans.py"}],
data_files=[("",extra_files),("bin",BIN),("coast",COAST),("doc",DOC),
("Microsoft.VC90.MFC", mfc_files),("Microsoft.VC90.CRT",crt_files),])
try:
	shutil.copytree("gdal","dist\\gdal")
except:
	print("Could not copy gdal installation")
try:
	os.rename("dist","GSTtrans")
except:
	pass
sys.exit()
