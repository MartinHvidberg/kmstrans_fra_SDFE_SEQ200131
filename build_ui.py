#!/usr/bin/python
import os,sys
os.chdir(os.path.dirname(__file__))
uis={"Trui.ui":"Main_gui.py",
"Dialog_settings_f2f.ui":"Dialog_settings_f2f.py",
"Dialog_layer_selector.ui":"Dialog_layer_selector.py",
"Tab_bshlm.ui":"Tab_bshlm.py",
"Tab_python.ui":"Tab_python.py",
"Dialog_settings_gdal.ui":"Dialog_settings_gdal.py",
"Dialog_creation_options.ui":"Dialog_creation_options.py"}
print("Building UIs...")
for ui in uis:
	f_in=os.path.join("UI",ui)
	f_out=uis[ui]
	if os.path.getmtime(f_in)<=os.path.getmtime(f_out):
		continue
	cmd="pyuic4 -o %s %s" %(f_out,f_in)
	print cmd
	rc=os.system(cmd)
	print("Return code: %d" %rc)
	

