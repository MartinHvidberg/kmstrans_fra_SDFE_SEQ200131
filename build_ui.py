#!/usr/bin/python
import os,sys
HERE=os.path.dirname(__file__)
if len(HERE)>0:
	os.chdir(HERE)
uis={"Trui.ui":"Main_gui.py",
"Launcher.ui":"Launcher.py",
"Dialog_settings_f2f.ui":"Dialog_settings_f2f.py",
"Dialog_layer_selector.ui":"Dialog_layer_selector.py",
"Tab_bshlm.ui":"Tab_bshlm.py",
"Tab_python.ui":"Tab_python.py",
"Dialog_settings_gdal.ui":"Dialog_settings_gdal.py",
"Affine_params.ui":"Widget_affine.py",
"Dialog_affine.ui":"Dialog_affine.py",
"Dialog_creation_options.ui":"Dialog_creation_options.py"}
print("Building UIs...")
for ui in uis:
	f_in=os.path.join("UI",ui)
	f_out=uis[ui]
	if os.path.exists(f_out) and os.path.getmtime(f_in)<=os.path.getmtime(f_out):
		continue
	cmd="pyuic4 -o %s %s" %(f_out,f_in)
	print cmd
	rc=os.system(cmd)
	print("Return code: %d" %rc)
f_in=os.path.join("UI","resources.qrc")
f_out="resources.py"
if (not os.path.exists(f_out)) or os.path.getmtime(f_out)<=os.path.getmtime(f_in):
	cmd="pyrcc4 -o %s %s" %(f_out,f_in)
	print cmd
	rc=os.system(cmd)
	print("Return code: %d" %rc)
	

