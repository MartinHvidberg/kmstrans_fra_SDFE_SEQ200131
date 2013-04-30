#!/usr/bin/python
import os,sys
os.chdir(os.path.dirname(__file__))
print("Building UIs...")
cmd="pyuic4 -o Main_gui.py -x %s" %(os.path.join("UI","GSTtrans.ui"))
print cmd
rc=os.system(cmd)
print("Return code: %d" %rc)
cmd="pyuic4 -o Dialog_settings_f2f.py %s" %(os.path.join("UI","Dialog_settings_f2f.ui"))
print cmd
rc=os.system(cmd)
print("Return code: %d" %rc)
cmd="pyuic4 -o Dialog_layer_selector.py %s" %(os.path.join("UI","Dialog_layer_selector.ui"))
print cmd
rc=os.system(cmd)
print("Return code: %d" %rc)
cmd="pyuic4 -o Dialog_creation_options.py %s" %(os.path.join("UI","Dialog_creation_options.ui"))
print cmd
rc=os.system(cmd)
print("Return code: %d" %rc)