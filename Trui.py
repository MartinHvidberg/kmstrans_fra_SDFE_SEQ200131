#!python
"""/*
* Copyright (c) 2012, National Survey and Cadastre, Denmark
* (Kort- og Matrikelstyrelsen), kms@kms.dk
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 */
 """
 #simlk, 2012-2015
 #Naming conventions - not totally PEP8 compliant, which is also the case for PyQt4
 #Thus - try to comply with the Qt4 style for methods: lowerUpper. See also: https://code.google.com/p/soc/wiki/PythonStyleGuide
 

 
import sys,os,time
import math
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from Main_gui import Ui_Trui
from BesselHelmert import BshlmWidget
from PythonConsole import PythonWidget
from Launcher import  Ui_LauncherWindow
from Dialog_settings_f2f import Ui_Dialog as Ui_Dialog_f2f
from Dialog_settings_gdal import Ui_Dialog as Ui_Dialog_gdal
from Dialog_layer_selector import Ui_Dialog as Ui_Dialog_layer_selector
from Dialog_creation_options import Ui_Dialog as Ui_Dialog_creation_options
from Dialog_affine import Ui_Dialog as Ui_Dialog_affine
from Widget_affine import Ui_Form as Ui_Widget_affine
import resources
import Minilabel
import TrLib
from TrLib_constants import *
import threading, subprocess
import File2File
import LibTrui

import WidgetUtils

try:
	import importlib
except ImportError:
	HAS_IMPORTLIB=False
else:
	HAS_IMPORTLIB=True

DEBUG="-debug" in sys.argv
#SEE IF WE ARE RUNNING PY2EXE OR SIMILAR#
try:
	sys.frozen
except:
	PREFIX=os.path.realpath(os.path.dirname(__file__))
else:
	PREFIX=os.path.realpath(os.path.dirname(sys.executable))
	DEBUG=False
os.chdir(PREFIX)
#SETUP SOME STANDARD PATHS
import platform
COMPANY_NAME="GST"  #Ahh, well, this migh change....
PROG_NAME="kmstrans2" #To not clash with earlier kmstrans??
IS_64_BIT="64" in platform.architecture()[0]
BIN_PREFIX=os.path.join(PREFIX,"bin")
TROGR=os.path.join(os.curdir,"bin",TROGRNAME)
#PATHS TO A MINIMAL DEFAULT GDAL INSTALLATION ON WINDOWS
GDAL_PREFIX=os.path.join(PREFIX,"gdal")
GDAL_DATA_PATH=os.path.join(GDAL_PREFIX,"gdal-data")
GDAL_PLUGIN_PATH=os.path.join(GDAL_PREFIX,"plugins")
GDAL_BIN_PATH=os.path.join(GDAL_PREFIX,"bin")
#OTHER PATHS
COAST_PREFIX=os.path.join(PREFIX,"coast")
COAST_PATH=os.path.join(COAST_PREFIX,"coast_world.shp")
PLUGIN_PATH_USER=os.path.expanduser(os.path.join("~","."+PROG_NAME,"plugins"))
PLUGIN_PATH_LOCAL=os.path.join(PREFIX,"plugins")
if not os.path.exists(PLUGIN_PATH_USER):
	try:
		os.makedirs(PLUGIN_PATH_USER)
	except:
		pass
DOC_PATH="file://"+PREFIX+"/"+"doc"
#POINTER TO WEB PAGES
URL_HELP_LOCAL=DOC_PATH+"/index.html"

#SAVE UNMODIFIED ENV
UNMODIFIED_ENV=os.environ.copy()

#DEFAULT DIR FOR FILE BROWSING - COULD BE STORED IN INI-FILE#
if "HOME" in os.environ:
	DEFAULT_DIR=os.environ["HOME"] #encoding can be problematic - cant assume it's ascii... thus use unicode conversion on saved Qt4 strings.
elif "HOMEPATH" in os.environ:
	DEFAULT_DIR=os.environ["HOMEPATH"]
else:
	DEFAULT_DIR="/"

#REQUIRED FILES IN GEOID DIR
REQUIRED_FILES=["def_lab.txt","manager.tab"]


VERSION="KMSTrans2 v2.2b2"

#SOME DEFAULT TEXT VALUES
ABOUT=VERSION+"""
\nWritten in PyQt4. File bugs at https://bitbucket.org/KMS/kmstrans/issues or send an email to simlk@gst.dk 
"""
MSG_GEOID_DIR="""
The selected directory MUST contain: 
def_lab.txt    (definition file for transformation system),
manager.tab (definition file for geoids),
AND the binary grid files defined in manager.tab

A valid geoid library is distributed by GST and should be downloadable e.g. from https://bitbucket.org/KMS/kmstrans/downloads
"""
#Custom events and threads# 
RENDER_COMPLETE=1234 #must be in betweeen MIN_USER and MAX_USER
FILE_LOG_EVENT=1235
RETURN_CODE_EVENT=1236

class MapEvent(QEvent):
	def __init__(self,etype=RENDER_COMPLETE):
		QEvent.__init__(self,etype)

class FileLogEvent(QEvent):
	def __init__(self,msg,etype=FILE_LOG_EVENT):
		QEvent.__init__(self,etype)
		self.msg=msg

class ReturnCodeEvent(QEvent):
	def __init__(self,rc,etype=RETURN_CODE_EVENT):
		QEvent.__init__(self,etype)
		self.rc=rc
		
class MessagePoster(object):
	def __init__(self,win):
		self.win=win
	def postFileMessage(self,text):
		event=FileLogEvent(text)
		app.postEvent(self.win,event)
	def postReturnCode(self,rc):
		event=ReturnCodeEvent(rc)
		app.postEvent(self.win,event)
		

class MapThread(threading.Thread):
	def __init__(self,win,region=REGION_DK):
		threading.Thread.__init__(self)
		self.win=win
		self.region=region #not used at the moment - for selecting coastline according to region....
	def run(self):
		lines=LibTrui.getLines(COAST_PATH)
		self.paths=[]
		for line in lines:
			path=QPainterPath(QPointF(line[0][0],-line[0][1]))
			for i in range(1,len(line)):
				path.lineTo(line[i][0],-line[i][1])
			self.paths.append(path)
		app.postEvent(self.win,MapEvent(RENDER_COMPLETE))


#Very very simple callback handling messages from TrLib and libtrui# 
def lordCallback(err_class,err_code,msg):
	try:
		MainWindow.displayCallbackMessage(msg.strip())
	except:
		pass

#Get a list of plugins - now from several paths. Enables plugins in root dir also
def getPlugins(plugin_paths):
	plugins=set()
	dublicates=set()
	for path in plugin_paths:
		if not os.path.exists(path):
			continue
		files=os.listdir(path)
		for name in files:
			location=os.path.join(path,name)
			if os.path.isdir(location):
				plugin_name=os.path.basename(name)
				if plugin_name in plugins:
					dublicates.add(plugin_name)
				else:
					plugins.add(plugin_name)
	return plugins,dublicates

#A class to keep cached output data#
class PointData(object):
	def __init__(self):
		self.is_valid=False
		self.has_scale=False
		self.coords=None
		self.mlb=None
		self.meridian_convergence=None
		self.scale=None
		self.proj_weakly_defined=False #flag for type 8 and 10 systems - right now detected on minilabel level. Would be great to expose the proj object (and thereby cstm code etc.)

#Hack to get scale and convergence for type 8 and 10 systems...
def getNumericScale(x1,y1,coord_transf,axis,flat):
	lon1,lat1,z=coord_transf.Transform(x1,y1)
	lat2=lat1+8e-5
	x2,y2,z=coord_transf.InverseTransform(lon1,lat2)
	d,a1,a2=TrLib.BesselHelmert(axis,flat,lon1,lat1,lon1,lat2)
	if (d is not None):
		dE=(x2-x1)
		dN=(y2-y1)
		sc=math.hypot(dE,dN)/d
		m=-math.atan2(dE,dN)*180.0/math.pi
	else:
		print("Exception during calculation of scale and convergence.") #or simply raise an exception
		sc,m=-1,-1
	return sc,m


			

class GDALSettings(object):
	""" Class which holds saved gdal settings """
	load_mode=0 #0,1 or 2 - 0: inlcuded, 1: system gdal (default except windows), 2: customized
	paths=["","",""]
	predefined_paths=[GDAL_BIN_PATH,GDAL_DATA_PATH,GDAL_PLUGIN_PATH]

class DialogGDALSettings(QtGui.QDialog,Ui_Dialog_gdal):
	def __init__(self,parent,settings):
		QtGui.QDialog.__init__(self,parent)
		self.settings=settings
		self.parent=parent
		self.dir=self.parent.dir
		self.setupUi(self)
		self.mode_buttons=[self.rdb_gdal_system,self.rdb_gdal_included,self.rdb_gdal_custom]
		self.txt_paths=[self.txt_bin_folder,self.txt_data_folder,self.txt_plugin_folder]
		self.browse_buttons=[self.bt_browse_bin,self.bt_browse_data,self.bt_browse_plugin]
		for bt in self.mode_buttons:
			bt.clicked.connect(self.onModeChange)
			if not IS_WINDOWS:
				bt.setEnabled(False)
		if not IS_WINDOWS:
			self.bt_apply.setEnabled(False)
		if settings.load_mode==0:
			self.rdb_gdal_system.setChecked(True)
		elif settings.load_mode==1:
			self.rdb_gdal_included.setChecked(True)
		else:
			self.rdb_gdal_custom.setChecked(True)
		self.onModeChange()
	def onModeChange(self):
		enable=not (self.rdb_gdal_system.isChecked() or self.rdb_gdal_included.isChecked())
		for field in self.txt_paths:
			field.setEnabled(enable)
		for bt in self.browse_buttons:
			bt.setEnabled(enable)
		if self.rdb_gdal_system.isChecked():
			self.txt_paths[0].setText("") #or ctypes.util.find_library("gdal")
			i=1
			for key in ["GDAL_DATA","GDAL_DRIVER_PATH"]:
				field=self.txt_paths[i]
				if key in os.environ:
					field.setText(os.environ[key])
				else:
					field.setText("not defined")
				i+=1
			return
		elif self.rdb_gdal_included.isChecked():
			paths=self.settings.predefined_paths
		else:
			paths=self.settings.paths
		for i in range(3):
			self.txt_paths[i].setText(paths[i])
	#TODO: implement this as a 'GetPath class' for reuse....
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_browse_bin_clicked(self):
		my_file = unicode(QFileDialog.getExistingDirectory(self, "Select a directory contaning gdal binaries.",self.dir))
		if len(my_file)>0:
			self.txt_paths[0].setText(my_file)
			self.dir=my_file
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_browse_data_clicked(self):
		my_file = unicode(QFileDialog.getExistingDirectory(self, "Select a directory containing gdal data files.",self.dir))
		if len(my_file)>0:
			self.txt_paths[1].setText(my_file)
			self.dir=my_file
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_browse_plugin_clicked(self):
		my_file = unicode(QFileDialog.getExistingDirectory(self, "Select a directory containing gdal plugins.",self.dir))
		if len(my_file)>0:
			self.txt_paths[2].setText(my_file)
			self.dir=my_file
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_apply_clicked(self):
		changes=False
		if self.rdb_gdal_system.isChecked():
			mode=0
		elif self.rdb_gdal_included.isChecked():
			mode=1
		else:
			mode=2
		if self.settings.load_mode!=mode:
			changes=True
			self.settings.load_mode=mode
		if mode==2:
			paths=[unicode(field.text()) for field in self.txt_paths]
			if paths!=self.settings.paths:
				changes=True
				self.settings.paths=paths
		if changes: 
			self.parent.saveSettings()
			QMessageBox.information(self,"GDAL settings","Changes will take effect after a restart.")
		self.accept()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_cancel_clicked(self):
		self.reject()

class AffineModifications(object):
	def __init__(self):
		self.input=LibTrui.AffineTransformation()
		self.output=LibTrui.AffineTransformation()
		self.apply_interactive=False
		self.apply_f2f=False
		self.input.apply=False
		self.output.apply=False

class AffineWidget(QtGui.QWidget,Ui_Widget_affine):
	"""Widget for editing affine parameters"""
	def __init__(self,parent,title,params):
		QtGui.QWidget.__init__(self,parent)
		self.setupUi(self)
		self.groupBox.setTitle(title)
		self.params=params
		self.chb_apply.setChecked(params.apply)
		self.R=[[self.r11,self.r12,self.r13],[self.r21,self.r22,self.r23],[self.r31,self.r32,self.r33]]
		self.T=[self.t1,self.t2,self.t3]
		self.setRotation(params.R)
		self.setTranslation(params.T)
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_reset_clicked(self):
		self.setRotation({})
		self.setTranslation({})
	@pyqtSignature('') #prevents actions being handled twice	
	def on_bt_invert_x_clicked(self):
		self.setRotation({(0,0):-1})
		self.setTranslation({})
		self.chb_apply.setChecked(True)
	def setRotation(self,R):
		for i in range(3):
			for j in range(3):
				if (i,j) in R:
					self.R[i][j].setText(str(R[(i,j)]))
				else:
					if (i!=j):
						self.R[i][j].setText("0")
					else:
						self.R[i][j].setText("1")
	def setTranslation(self,T):
		for i in range(3):
			if i in T:
				self.T[i].setText(str(T[i]))
			else:
				self.T[i].setText("0")
	def getTranslation(self):
		vals={}
		for i in range(3):
			v=unicode(self.T[i].text())
			if len(v)>0:
				try:
					v=float(v.replace(",","."))
				except:
					self.T[i].setFocus()
					QMessageBox.warning(self,"Error","Specify a numeric input")
					return None
				if v!=0.0:
					vals[i]=v
		return vals
	def getRotation(self):
		vals={}
		for i in range(3):
			for j in range(3):
				v=unicode(self.R[i][j].text())
				if len(v)>0:
					try:
						v=float(v.replace(",","."))
					except:
						self.R[i][j].setFocus()
						QMessageBox.warning(self,"Error","Specify a numeric input")
						return None
					if (i==j and v!=1.0) or (i!=j and v!=0.0):
						vals[(i,j)]=v
		return vals
	def setParameters(self):
		self.params.apply=bool(self.chb_apply.isChecked())
		R=self.getRotation()
		if R is not None:
			self.params.R=R
		else:
			self.params.R={}
		T=self.getTranslation()
		if T is not None:
			self.params.T=T
		else:
			self.params.T={}
		self.params.setup()
	
				
				
				
				

class DialogSetupAffine(QtGui.QDialog,Ui_Dialog_affine):
	"""Class for setting up affine transformation"""
	def __init__(self,parent,params):
		QtGui.QDialog.__init__(self,parent)
		self.setupUi(self)
		self.affine_in=AffineWidget(self,"Modify input",params.input)
		#self.affine_in.chb_apply.toggled.connect(self.onEnableAffine) #check event propagation!
		self.affine_out=AffineWidget(self,"Modify output",params.output)
		self.layout_horizontal.addWidget(self.affine_in)
		self.layout_horizontal.addWidget(self.affine_out)
		self.params=params
		self.chb_apply_f2f.setChecked(params.apply_f2f)
		self.chb_apply_interactive.setChecked(params.apply_interactive)
	
		
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_cancel_clicked(self):
		self.reject()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_apply_clicked(self):
		#make sure that we can only return ACCEPT in a consistent state.
		#i.e. if no real affine modifacations - we cannot apply in one of the tabs.
		#and non-trivial mods which are not applied should also trigger message.
		nvals=0
		#first check if a modification is set
		for widget,name in [(self.affine_in,"input"),(self.affine_out,"output")]:
			do_apply=widget.chb_apply.isChecked()
			if do_apply: #only save if apply is checked...
				R=widget.getRotation()
				if R is None:
					return
				T=widget.getTranslation()
				if T is None:
					return
				#TODO: handle the situatuon where one the transormations is trivial...
				vals_here=len(R)+len(T)
				if vals_here==0:
					msg="Affine modification enabled in "+name+"- but no nontrivial values set."
					QMessageBox.information(self,"Affine setup",msg)
					widget.setFocus()
					return
				nvals+=vals_here
		if (self.chb_apply_f2f.isChecked() or self.chb_apply_interactive.isChecked()):
			if nvals==0:
				QMessageBox.information(self,"Affine setup","No nontrivial modifications to apply. Cancel or set some!")
				return
		else:
			if nvals>0:
				QMessageBox.information(self,"Affine setup","You have enabled affine modificaitions, but they are not applied in any tab.")
				return
		#in a consistent state and ready to fly, so modify stored params.
		self.params.apply_f2f=bool(self.chb_apply_f2f.isChecked())
		self.params.apply_interactive=bool(self.chb_apply_interactive.isChecked())
		for widget in (self.affine_in,self.affine_out):
			widget.setParameters()
		self.accept()
		
		
			
class DialogFile2FileSettings(QtGui.QDialog,Ui_Dialog_f2f):
	"""Class for specifying options to TEXT and KMS drivers"""
	def __init__(self,parent,settings):
		QtGui.QDialog.__init__(self,parent)
		self.setupUi(self)
		self.chbs=[self.chb_whitespace,self.chb_space,self.chb_tab,self.chb_semicolon,self.chb_comma,self.chb_pattern,
		self.chb_output_units,self.chb_has_z,self.chb_invert_xy,self.chb_crt_xyz,self.chb_lazyh,self.chb_copy_bad,
		self.chb_kms_no_units,self.chb_kms_flip_input,self.chb_kms_flip_output]
		self.rdbs=[self.rdb_dg,self.rdb_sx,self.rdb_nt,self.rdb_rad,self.rdb_dg_in,self.rdb_sx_in,self.rdb_nt_in,self.rdb_rad_in]
		self.text_fields=[self.txt_pattern,self.txt_comments]
		self.spbs=[self.spb_col_x,self.spb_col_y,self.spb_col_z]
		self.settings=settings
		self.restoreSavedState()
		self.settings.accepted=False
	#TODO: implement save and load settings like in MainWindow - should also *always* display the current settings, so that the cancel button should uncheck/recheck stuff.
	def restoreSavedState(self):
		i=0
		for val in self.settings.saved_state_chbs:
			self.chbs[i].setChecked(val)
			i+=1
		i=0
		for val in self.settings.saved_state_rdbs:
			if val:
				self.rdbs[i].setChecked(True)
			i+=1
		i=0
		for val in self.settings.saved_state_spbs:
			self.spbs[i].setValue(val)
			i+=1
		i=0
		for val in self.settings.saved_state_text:
			self.text_fields[i].setText(val)
			i+=1
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_close_clicked(self):
		self.reject()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_apply_clicked(self):
		ok=self.apply()
		if ok:
			self.accept()
	def apply(self):
		col_x=self.spb_col_x.value()
		col_y=self.spb_col_y.value()
		if self.chb_has_z.isChecked():
			col_z=self.spb_col_z.value()
		else:
			col_z=None
		if  col_x==col_y or col_x==col_z or col_y==col_x or col_y==col_z:
			self.message("Geometry columns must differ!")
			return False
		sep_char=""
		if self.chb_whitespace.isChecked():
			sep_char+=" \\t"
		else:
			if self.chb_space.isChecked():
				sep_char+=" "
			if self.chb_tab.isChecked():
				sep_char+="\\t"
		if self.chb_comma.isChecked():
			sep_char+=","
		if self.chb_semicolon.isChecked():
			sep_char+=";"
		if self.chb_pattern.isChecked():
			sc=str(self.txt_pattern.text()).strip()
			if len(sc)==0:
				#Do something#
				self.message("Specify separation chars.")
				self.txt_pattern.setFocus()
				return False
			sep_char+=sc
		if sep_char=="":
			self.message("Specify column separation chars.")
			return False
		comments=str(self.txt_comments.text()).strip()
		if len(comments)>0:
			self.settings.comments=comments
		else:
			self.settings.comments=None
		self.settings.units_in_output=bool(self.chb_output_units.isChecked())
		self.settings.kms_no_units= bool(self.chb_kms_no_units.isChecked())
		self.settings.flip_xy=bool(self.chb_invert_xy.isChecked())
		self.settings.kms_flip_xy_in=bool(self.chb_kms_flip_input.isChecked())
		self.settings.kms_flip_xy_out=bool(self.chb_kms_flip_output.isChecked())
		self.settings.crt_xyz=bool(self.chb_crt_xyz.isChecked())
		self.settings.copy_bad_lines=bool(self.chb_copy_bad.isChecked())
		self.settings.lazyh=bool(self.chb_lazyh.isChecked())
		self.settings.output_geo_unit="dg"
		if self.rdb_sx.isChecked():
			self.settings.output_geo_unit="sx"
		elif self.rdb_nt.isChecked():
			self.settings.output_geo_unit="nt"
		elif self.rdb_rad.isChecked():
			self.settings.output_geo_unit="rad"
		self.settings.input_geo_unit="dg"
		if self.rdb_sx_in.isChecked():
			self.settings.input_geo_unit="sx"
		elif self.rdb_nt_in.isChecked():
			self.settings.input_geo_unit="nt"
		elif self.rdb_rad_in.isChecked():
			self.settings.input_geo_unit="rad"
		#else get the stuff from other boxes...#
		self.settings.col_x=col_x
		self.settings.col_y=col_y
		self.settings.col_z=col_z
		self.settings.sep_char=sep_char
		self.settings.accepted=True
		self.settings.saved_state_chbs=[]
		self.settings.saved_state_rdbs=[]
		self.settings.saved_state_spbs=[]
		self.settings.saved_state_text=[]
		for obj in self.chbs:
			self.settings.saved_state_chbs.append(obj.isChecked())
		for obj in self.rdbs:
			self.settings.saved_state_rdbs.append(obj.isChecked())
		for obj in self.text_fields:
			self.settings.saved_state_text.append(obj.text())
		for obj in self.spbs:
			self.settings.saved_state_spbs.append(obj.value())
		
		return True
	def message(self,text,title="Error"):
		QMessageBox.warning(self,title,text)

class DialogCreationOptions(QDialog,Ui_Dialog_creation_options):
	"""Class for specifying creation options OGR drivers"""
	def __init__(self,parent,driver,drivers):
		QtGui.QDialog.__init__(self,parent)
		self.driver=driver
		self.drivers=drivers
		self.setupUi(self)
		self.lbl_format.setText(driver)
		if driver in drivers:
			short,dco,lco=drivers[driver]
			self.lbl_format_short.setText(short)
			self.txt_dco.setText(dco)
			self.txt_lco.setText(lco)
		else:
			self.lbl_format_short.setText("Not defined!")
	def accept(self):
		#driver: ["name",lco,dco]
		if self.driver in self.drivers:
			dco=str(self.txt_dco.text()).strip()
			lco=str(self.txt_lco.text()).strip()
			if len(dco)>0:
				if self.validate(dco):
					self.drivers[self.driver][1]=dco
				else:
					self.txt_dco.setFocus()
					return
			else:
				self.drivers[self.driver][1]=""
			if len(lco)>0:
				if self.validate(lco):
					self.drivers[self.driver][2]=lco
				else:
					self.txt_lco.setFocus()
					return
			else:
				self.drivers[self.driver][2]=""
		self.done(0)
	def validate(self,text):
		cops=text.split(",")
		for item in cops:
			if len(item.split("="))!=2:
				self.message("Bad format of creation option %s, should be 'KEY=VALUE'" %item)
				return False
		return True
	def message(self,text,title="Error"):
		QMessageBox.warning(self,title,text)
		
	
		

class TextViewer(QDialog):
	"""Class to display text files"""
	def __init__(self,parent,txt=None,fname=None):
		QDialog.__init__(self,parent)
		self.setWindowTitle("Text Viewer")
		self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		txt_field=QTextEdit(self)
		txt_field.setCurrentFont(QFont("Courier",9))
		txt_field.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		txt_field.setReadOnly(True)
		txt_field.setMinimumSize(600,200)
		#self.setMinimumSize(600,400)
		layout=QVBoxLayout(self)
		layout.addWidget(txt_field)
		if txt is not None:
			txt_field.setText(txt)
		elif fname is not None:
			fok=False
			if os.path.exists(fname):
				try:
					n=os.path.getsize(fname)
				except:
					pass
				else:
					fok=True
			if not fok:
				txt_field.setText("Failed to open %s" %fname)
			else:
				txt_field.setText("Contents of %s:" %fname)
				if n/1024>100:
					maxlines=1000
					txt_field.append("***Large file - will only display the first %d lines:\n" %maxlines)
				else:
					maxlines=None
				f=open(fname)
				nlines=0
				txt=""
				line=f.readline()
				while len(line)>0 and (maxlines is None or nlines<maxlines):
					txt+=line
					line=f.readline()
					nlines+=1
				txt_field.append(txt)
				f.close()
		
		self.setLayout(layout)
		self.adjustSize()


class LayerSelector(QDialog, Ui_Dialog_layer_selector):
	def __init__(self,parent,layers,txt_field):
		QtGui.QDialog.__init__(self,parent)
		self.setupUi(self)
		for layer in layers:
			self.listWidget.addItem(layer)
		#for layer_number in range(len(layers)):
		#	self.listWidget.setItemSelected(self.listWidget.item(layer_number),True)
		self.txt_field=txt_field
		self.adjustSize()
	def accept(self):
		txt=""
		items=self.listWidget.selectedItems()
		for i in range(len(items)):
			item=items[i]
			txt+=str(item.text())
			if i<len(items)-1:
				txt+=";"
		self.txt_field.setText(txt)
		self.done(0)

	
class RedirectOutput(object):
	def __init__(self,method):
		self.method=method
		self.buffer=""
	def write(self,text):
		self.buffer+=text
		if self.buffer[-1]=="\n":
			self.flush()
	def flush(self):
		if len(self.buffer)==0:
			return
		if self.buffer[-1]=="\n":
			self.method(self.buffer[:-1])
		else:
			self.method(self.buffer)
		self.buffer=""
		

def initTransformationLibrary():
	#init TrLib and load settings#
	ok,msg=TrLib.LoadLibrary(TRLIB,BIN_PREFIX)
	if not ok:
		if not os.path.exists(BIN_PREFIX):
			msg+="\nDid you build binaries?"
		else:
			msg+="\nYou may need to rebuild libraries..."
		return False,msg
	TrLib.SetMessageHandler(lordCallback)
	TrLib.SetMaxMessages(-1)
	TrLib.SetThreadMode(False)
	#Will still need to set geoid library before  TrLib is fully initialised!
	return True,msg

class LauncherWindow(QtGui.QMainWindow,Ui_LauncherWindow):
	def __init__(self,parent=None):
		QtGui.QMainWindow.__init__(self,parent) 
		self.setupUi(self)
		self.setWindowIcon(QIcon(":/UI/icon.png"))
		self.log("Launcher window for %s" %VERSION,"blue")
		ok,msg=initTransformationLibrary()
		self.geoids=None
		if not ok:
			self.log("Unable to load transformation library!","red")
			self.log(msg,"red")
			self.log("KMSTrans2 will not be able to start...","red")
			self.log("See https://bitbucket.org/KMS/kmstrans/wiki/Home for build instructions...","blue")
			self.bt_launch.setEnabled(False)
			self.bt_geoids.setEnabled(False)
			self.show()
		else:	
			self.log("Transformation library loaded...","blue")
			self.log("Version: %s" %TrLib.GetVersion(),"blue")
			self.log("Loading settings...","blue")
			settings = QSettings(COMPANY_NAME,PROG_NAME)
			settings.beginGroup('data')
			geoids=settings.value('geoids')
			if geoids.isValid():
				try:
					self.geoids=unicode(geoids.toString())
				except:
					self.log("Encoding error for stored geoid dir.\n","red")
					
			if self.geoids is None and "TR_TABDIR" in os.environ:
				self.geoids=os.environ["TR_TABDIR"]
			if self.geoids is None:
				self.log("Geoid library not set.","red")
				self.log("Please select a valid geoid library.","blue")
				self.log(MSG_GEOID_DIR,"brown")
				self.bt_launch.setEnabled(False)
				self.show()
			else:
				self.log("Geoid directory currently set to: %s" %self.geoids,"blue")
				ok=self.setGeoidLibrary()
				if ok:
					self.launch()
				else:
					self.show()
	def launch(self):
		global MainWindow
		MainWindow=TRUI(geoids=self.geoids)
		self.close() #hmm this only closes the window - its not deleted. Seems to be sufficient for the app to shut down though...
	def log(self,text,color="black",clear=False):
		self.txt_log.setTextColor(QColor(color))
		if clear:
			self.txt_log.setText(text)
		else:
			self.txt_log.append(text)
		self.txt_log.ensureCursorVisible()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_launch_clicked(self):
		self.launch()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_geoids_clicked(self):
		gdir = unicode(QFileDialog.getExistingDirectory(self, "Select a valid geoid directory","/"))
		if (gdir is None or len(gdir)==0):
			return
		for name in REQUIRED_FILES:
			if not os.path.exists(os.path.join(gdir,name)):
				self.log("Required file %s not found in %s" %(name,gdir),"red")
				return
		self.geoids=gdir
		ok=self.setGeoidLibrary()
		if ok:
			self.log("Successfull initialisation using geoid library from %s" %gdir,"blue")
			self.bt_launch.setEnabled(True)
			self.log("KMSTrans2 is ready to be launched!","blue")
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_close_clicked(self):
		self.close()
		#sys.exit()
	def setGeoidLibrary(self):
		try:
			ok=TrLib.InitLibrary(self.geoids,None,None)
		except Exception, e_value:
			self.log("Failed to initialise with selected geoid directory\nError:\n%s" %(str(e_value)))
		else:
			if ok:
				return True
		return False
			
		
		

class TRUI(QtGui.QMainWindow,Ui_Trui):
	def __init__(self,parent=None,geoids=None):
		QtGui.QMainWindow.__init__(self,parent) 
		self.setupUi(self)
		self.geoids=geoids
		self._save_settings=False #flag which signals whether to save settings - only do it if initialisation succeded!
		self._clear_log=False #flag to signal whether to clear interactive log before each transformation
		#APPEARANCE#
		self.setWindowIcon(QIcon(":/UI/icon.png"))
		self.setWindowTitle(VERSION)
		#Set log methods - tabs work as general plugins do#
		self.tab_interactive.handleStdOut=self.logInteractiveStdout
		self.tab_interactive.handleStdErr=self.logInteractiveStderr
		self.tab_interactive.handleCallBack=self.logInteractiveCallBack
		self.tab_ogr.handleStdOut=self.logF2Fstdout
		self.tab_ogr.handleStdErr=self.logF2FStderr
		self.tab_ogr.handleCallBack=self.logF2FCallback
		#Set up event handlers#
		#some event handlers defined directly by special method names#
		self.cb_input_system.currentIndexChanged.connect(self.onSystemInChanged)
		self.cb_output_system.currentIndexChanged.connect(self.onSystemOutChanged)
		self.cb_f2f_input_system.currentIndexChanged.connect(self.onF2FSystemInChanged)
		self.cb_f2f_output_system.currentIndexChanged.connect(self.onF2FSystemOutChanged)
		self.chb_show_scale.clicked.connect(self.onShowScale)
		self.bt_interactive_transform.clicked.connect(self.transformInput)
		self.chb_f2f_label_in_file.toggled.connect(self.onF2FSystemInChanged)
		self.rdobt_f2f_ogr.toggled.connect(self.onRdobtOGRToggled)
		#self.chb_f2f_apply_affine.toggled.connect(self.onF2FApplyAffine)
		#self.chb_apply_affine.toggled.connect(self.onInteractiveApplyAffine)
		#Menu event handlers#
		self.actionNew_KMSTrans.triggered.connect(self.onNewKMSTrans)
		self.actionExit.triggered.connect(self.onExit)
		self.actionAbout_KMSTrans.triggered.connect(self.onAbout)
		self.actionHelp_local.triggered.connect(self.onHelpLocal)
		self.actionDK.triggered.connect(self.setRegionDK)
		self.actionFO.triggered.connect(self.setRegionFO)
		self.actionGR.triggered.connect(self.setRegionGR)
		self.actionWorld.triggered.connect(self.setRegionWorld)
		self.actionDegrees.triggered.connect(self.setAngularUnitsDegrees)
		self.actionRadians.triggered.connect(self.setAngularUnitsRadians)
		self.actionNt.triggered.connect(self.setAngularUnitsNt)
		self.actionSx.triggered.connect(self.setAngularUnitsSx)
		self.actionDegrees_derived.triggered.connect(self.setDerivedAngularUnitsDegrees)
		self.actionRadians_derived.triggered.connect(self.setDerivedAngularUnitsRadians)
		self.actionNt_derived.triggered.connect(self.setDerivedAngularUnitsNt)
		self.actionSx_derived.triggered.connect(self.setDerivedAngularUnitsSx)
		self.actionGeoid_directory.triggered.connect(self.changeTabDir)
		self.actionFile2file_settings.triggered.connect(self.openFile2FileSettings)
		self.actionGDAL_settings.triggered.connect(self.openGDALSettings)
		self.actionPlugins_enabled.triggered.connect(self.togglePluginsEnabled)
		self.actionSetup_affine_modifications.triggered.connect(self.setupAffine)
		#end setup event handlers#
		#Set up convienient pointers to input and output#
		self.input=[self.txt_x_in,self.txt_y_in,self.txt_z_in]
		self.input_labels=[self.lbl_x_in,self.lbl_y_in,self.lbl_z_in]
		self.output=[self.txt_x_out,self.txt_y_out,self.txt_z_out]
		self.output_labels=[self.lbl_x_out,self.lbl_y_out,self.lbl_z_out]
		self.derived_angular_output=[self.txt_meridian_convergence] #+self.output_bshlm_azimuth[1:]
		self.action_angular_units={ANGULAR_UNIT_DEGREES:self.actionDegrees,ANGULAR_UNIT_RADIANS:self.actionRadians,
		ANGULAR_UNIT_SX:self.actionSx,ANGULAR_UNIT_NT:self.actionNt}
		self.action_angular_units_derived={ANGULAR_UNIT_DEGREES:self.actionDegrees_derived,ANGULAR_UNIT_RADIANS:self.actionRadians_derived,
		ANGULAR_UNIT_SX:self.actionSx_derived,ANGULAR_UNIT_NT:self.actionNt_derived}
		#SET UP INPUT EVENT HANDLERS: TRANSFORM ON RETURN. TODO: ADD VALIDATOR#
		for field in self.input:
			field.returnPressed.connect(self.transformInput)
		#END SETUP INPUT EVENT HANDLERS#
		#Create Whatsthis in help menu#
		self.menuHelp.addSeparator()
		self.menuHelp.addAction(QWhatsThis.createAction(self))
		#SETUP VARIOUS ATTRIBUTES#
		self.coord_precision=4 # 4 decimals in metric output - translates to something else for angular output...
		self.affine_modifications=AffineModifications()
		self.message_poster=MessagePoster(self)
		self.f2f_settings=File2File.F2F_Settings()
		self.f2f_settings.n_decimals=self.coord_precision
		self.output_cache=PointData()
		self.mlb_in=None #New attribute - used to test whether we should upodate system info....
		self.geo_unit=ANGULAR_UNIT_DEGREES
		self.setAngularUnitsDegrees()
		self.geo_unit_derived=ANGULAR_UNIT_DEGREES
		self.setDerivedAngularUnitsDegrees()
		self.region=REGION_DK #will also be set in loadSettings - TODO: save and load other settings...
		self._handle_system_change=True
		self.point_center=[0,0]
		self.map_zoom=0
		try:
			sys.frozen
		except:
			pass
		else:
			self.logInteractive("Running through py2exe.")
		#move to interactive tab - messages will appear there afterwards,,,,#
		try:
			self.main_tab_host.setCurrentIndex(0)
		except:
			pass
		#redirect python output#
		sys.stdout=RedirectOutput(self.handleStdOut)
		#Load settings NOW#
		#Will setup various attributes and determine e.g. if we are running a local gdal installation#
		#It's complicated but we need to set the env variables BEFORE loading the first shared library (except for PATH).
		#Otherwise, e.g. the variable GDAL_DRIVER_PATH, if set AFTER the first load, WONT be passed on the load of the second library.
		#Has to do with the way different crts and win apis handle env variables. And maybe something internal to the way ctypes handles these.
		#See: http://bugs.python.org/issue16633
		self.loadSettings()
		load_mode=self.gdal_settings.load_mode
		if IS_WINDOWS:
			#this is also needed in order to fix the library dependecies in the bin subfolder#
			path=os.environ["PATH"] #a mbcs encoded str
			path=BIN_PREFIX+os.pathsep+path 
			if (load_mode==1 or load_mode==2):
				if load_mode==1:
					paths=self.gdal_settings.predefined_paths #mcbs encoded strs
				else:
					paths=[p.encode(sys.getfilesystemencoding()) for p in self.gdal_settings.paths] #unicode objects
				path=paths[0]+os.pathsep+path
				os.environ["GDAL_DATA"]=paths[1]
				os.environ["GDAL_DRIVER_PATH"]=paths[2]
			os.environ["PATH"]=path
		#initialise the map#
		self.initMap()
		#load OGR dependent things...
		self.loadLibtrui()
		#important to set this var which will be passed on to trogr when running batch mode 
		os.environ["TR_TABDIR"]=self.geoids.encode(sys.getfilesystemencoding())
		#Now that trlib is initlialised we can define these tranformation objects#
		self.initTransformations()
		self.lbl_geoid_dir_value.setText(os.path.realpath(self.geoids))
		#Setup BSHLM tab#
		self.tab_bshlm=BshlmWidget(self)
		self.main_tab_host.addTab(self.tab_bshlm,"Bessel Helmert")
		#Setup Python Console tab#
		self.tab_python=PythonWidget(self)
		self.main_tab_host.addTab(self.tab_python,"Python console")
		#Load plugins#
		if self.enable_plugins:
			self.actionPlugins_enabled.setText("Disable plugins")
			self.loadPlugins()
		else:
			self.actionPlugins_enabled.setText("Enable plugins")
			self.logInteractive("Plugins disabled...",color="brown")
		#Only now - redirect python stderr - to be able to see errors in the initialisation#
		self.initRegion()
		sys.stderr=RedirectOutput(self.handleStdErr)
		self._save_settings=True #flag which signals whether to save settings - only do it if initialisation succeded - so now it's ok!
		self._clear_log=True
		self.show()
	def closeTransformations(self):
		if self.numeric_scale_transf is not None:
			self.numeric_scale_transf.close()
		if self.coordinate_transformation is not None:
			self.coordinate_transformation.close()
		if self.map_transformation is not None:
			self.map_transformation.close()
	def initTransformations(self):
		self.numeric_scale_transf=TrLib.CoordinateTransformation("","geo_etrs89")
		self.fallback_ellipsoid=TrLib.GetEllipsoidParametersFromDatum("etrs89")
		self.coordinate_transformation=TrLib.CoordinateTransformation("","")
		#Initialse the map transformation#
		self.map_transformation=TrLib.CoordinateTransformation("geo_wgs84","geo_wgs84")
	def onExit(self):
		self.close()
	def onActionWhatsThis(self):
		QWhatsThis.enterWhatsThisMode()
	def onHelpLocal(self):
		try:
			import webbrowser
			webbrowser.open(URL_HELP_LOCAL)
		except Exception,msg:
			self.message("Failed to help page in web browser:\n"+repr(msg))
	def onAbout(self):
		msg=ABOUT+"\nTransformation engine:\n%s"%TrLib.GetVersion()
		QMessageBox.about(self,"About "+PROG_NAME,msg)
	def openFile2FileSettings(self):
		dlg=DialogFile2FileSettings(self,self.f2f_settings)
		dlg.exec_()
	def openGDALSettings(self):
		dlg=DialogGDALSettings(self,self.gdal_settings)
		dlg.exec_()
	def onNewKMSTrans(self):
		subprocess.Popen([sys.executable,sys.argv[0]],env=UNMODIFIED_ENV)
		self.logInteractive("Starting new process")
	#Map Stuff#	
	def initMap(self):
		self.scene=QtGui.QGraphicsScene(self.gv_map)
		self.gv_map.setScene(self.scene)
		self.gv_map.setInteractive(True)
		self.gv_map.setDragMode(QGraphicsView.ScrollHandDrag)
		self.scene.setSceneRect(-180,-90,360,180)
		self.scene.addLine(-180,0,180,0)
		self.scene.addLine(0,90,0,-90)
		self.map_point=QtGui.QGraphicsEllipseItem(0,0,10,10)
		self.map_point.setBrush(QtGui.QBrush(QColor(255, 10, 10, 200)))
		self.scene.addItem(self.map_point) #always add it - then we can remove and add again later
		
	def customEvent(self,event):
		if int(event.type())==RENDER_COMPLETE:
			paths=self.mapthread.paths
			self.logInteractive("Load of coastline completed. Rendering...")
			t1=time.clock()
			self.scene.removeItem(self.map_point)
			for path in paths:
				self.scene.addPath(path)
			t2=time.clock()
			if DEBUG:
				self.logInteractive("Render time: %.4f s" %(t2-t1))
			self.scene.addItem(self.map_point)
		if int(event.type())==FILE_LOG_EVENT:
			self.logF2F(event.msg)
		if int(event.type())==RETURN_CODE_EVENT:
			self.onF2FReturnCode(event.rc)
			

	def drawPoint(self,x,y,z,mlb_in):
		if self.map_transformation.mlb_in!=mlb_in:
			self.map_transformation.Insert(mlb_in)
		try:
			x,y,z=self.map_transformation.TransformPoint(x,y,z)
		except:
			self.map_point.setBrush(QtGui.QBrush(QColor(255, 10, 10, 90)))
			self.logInteractive("Error in map transformation - failed to draw map point","red")
		else:
			self.map_point.setBrush(QtGui.QBrush(QColor(255, 10, 10, 200)))
			r=2**(-self.map_zoom)*10
			self.map_point.setPos(x-r*0.5,-y-r*0.5)
			self.map_coords=(x,y)
			self.scene.update()
		
		#TODO: consider enabling this redraw of map-canvas on transformation....
		#if (self.chb_zoom_to_point.isChecked() and self.map_zoom>0):
		#	self.gv_map.centerOn(self.map_point)
		
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_zoom_in_clicked(self):
		if self.map_zoom>7:
			return
		self.map_zoom+=1
		self.zoomMap()
		
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_zoom_out_clicked(self):
		if self.map_zoom<=0:
			return
		self.map_zoom-=1
		self.zoomMap()
		
	def zoomMap(self):
		self.gv_map.setMatrix(QMatrix(2**(self.map_zoom),0,0,2**(self.map_zoom),0,0))
		r=2**(-self.map_zoom)
		x,y=self.map_coords
		self.map_point.setPos(x-r*5,-y-r*5)
		self.map_point.setScale(r)
		if (self.chb_zoom_to_point.isChecked()):
			self.gv_map.centerOn(self.map_point)
		self.scene.update()
		
	
	def initRegion(self):
		self._handle_system_change=False
		systems,init_coords,region_name=REGIONS[self.region]
		self.lbl_region_value.setText(region_name)
		self.cb_input_system.clear()
		self.cb_output_system.clear()
		self.cb_f2f_input_system.clear()
		self.cb_f2f_output_system.clear()
		self.cb_f2f_input_system.addItems(systems)
		self.cb_f2f_output_system.addItems(systems)
		self.cb_input_system.addItems(systems)
		self.cb_output_system.addItems(systems)
		self.setInteractiveInput(init_coords)
		self.cb_input_system.setCurrentIndex(0) #TODO: dont emit signal!
		self.cb_output_system.setCurrentIndex(0)
		self._handle_system_change=True
		self.transformInput() #this should trigger the redraw of the point
		self.zoomMap()
		for widget in self.getAdditionalWidgets():
			if hasattr(widget,"handleRegionChange"):
				widget.handleRegionChange(self.region)
		
	def onSystemInChanged(self):
		if not self._handle_system_change:
			return
		#Trigger a transformation#
		self.transformInput(True,False)
		
	
	def onSystemOutChanged(self):
		if not self._handle_system_change:
			return
		#Trigger a transformation#
		self.transformInput(False,True)
		
			
	def setSystemInfo(self,do_input=True,do_output=False):
		if do_input:
			mlb_in=str(self.cb_input_system.currentText())
			text=TrLib.DescribeLabel(mlb_in)
			if self.affine_modifications.apply_interactive and self.affine_modifications.input.apply:
				text+=",+affine modification"
			self.lbl_input_info.setText("Input system info: %s" %text)
			labels=Minilabel.getSystemLabels(mlb_in)
			if labels is not None:
				for i in range(3):
					self.input_labels[i].setText(labels[i])
		if do_output:
			mlb_out=str(self.cb_output_system.currentText())
			text=TrLib.DescribeLabel(mlb_out)
			if self.affine_modifications.apply_interactive and self.affine_modifications.output.apply:
				text+=",+affine modification"
			self.lbl_output_info.setText("Output system info: %s" %text)
			labels=Minilabel.getSystemLabels(mlb_out)
			if labels is not None:
				for i in range(3):
					self.output_labels[i].setText(labels[i])
		
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_change_h_in_clicked(self):
		mlb_in=str(self.cb_input_system.currentText())
		mlb=Minilabel.changeHeightSystem(mlb_in,H_SYSTEMS[self.region],DATUM_ALLOWED_H_SYSTEMS,False)
		if mlb!=mlb_in:
			self.cb_input_system.setEditText(mlb)
			self.transformInput(True,False)
		
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_change_h_out_clicked(self):
		mlb_out=str(self.cb_output_system.currentText())
		mlb=Minilabel.changeHeightSystem(mlb_out,H_SYSTEMS[self.region],DATUM_ALLOWED_H_SYSTEMS)
		if mlb!=mlb_out:
			self.cb_output_system.setEditText(mlb)
			self.transformInput(False,True)
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_interactive_swap_clicked(self):
		#Transform - then swap input/output
		#TODO - consider how to handle affine modifications on a swap. Perhaps failing is ok... 
		#OR we can flip the affine modifications also...
		self.transformInput()
		if self.output_cache.is_valid:
			self._handle_system_change=False
			mlb_in=str(self.cb_input_system.currentText())
			mlb_out=self.output_cache.mlb
			self.setInteractiveInput(self.output_cache.coords,mlb_out)
			self.cb_input_system.setEditText(mlb_out)
			self.cb_output_system.setEditText(mlb_in)
			self._handle_system_change=True
			self.transformInput()
			if self.affine_modifications.apply_interactive:
				self.logInteractive("NOTE: Systems have been interchanged - but not the affine modifications.","blue")
	def setRegionDK(self):
		if self.region!=REGION_DK:
			self.region=REGION_DK
			self.initRegion()
	def setRegionFO(self):
		if self.region!=REGION_FO:
			self.region=REGION_FO
			self.initRegion()
	def setRegionGR(self):
		if self.region!=REGION_GR:
			self.region=REGION_GR
			self.initRegion()
	def setRegionWorld(self):
		if self.region!=REGION_WORLD:
			self.region=REGION_WORLD
			self.initRegion()
	def setAngularUnitsDegrees(self):
		if self.geo_unit!=ANGULAR_UNIT_DEGREES:
			self.geo_unit=ANGULAR_UNIT_DEGREES
			self.translateGeoUnits()
		self.action_angular_units[ANGULAR_UNIT_DEGREES].setChecked(True)
		self.lbl_geo_coords_value.setText("%3s" %ANGULAR_UNIT_DEGREES)
	def setAngularUnitsRadians(self):
		if self.geo_unit!=ANGULAR_UNIT_RADIANS:
			self.geo_unit=ANGULAR_UNIT_RADIANS
			self.translateGeoUnits()
		self.action_angular_units[ANGULAR_UNIT_RADIANS].setChecked(True)
		self.lbl_geo_coords_value.setText("%3s" %ANGULAR_UNIT_RADIANS)
	def setAngularUnitsNt(self):
		if self.geo_unit!=ANGULAR_UNIT_NT:
			self.geo_unit=ANGULAR_UNIT_NT
			self.translateGeoUnits()
		self.action_angular_units[ANGULAR_UNIT_NT].setChecked(True)
		self.lbl_geo_coords_value.setText("%3s" %ANGULAR_UNIT_NT)
	def setAngularUnitsSx(self):
		if self.geo_unit!=ANGULAR_UNIT_SX:
			self.geo_unit=ANGULAR_UNIT_SX
			self.translateGeoUnits()
		self.action_angular_units[ANGULAR_UNIT_SX].setChecked(True)
		self.lbl_geo_coords_value.setText("%3s" %ANGULAR_UNIT_SX)
	def setDerivedAngularUnitsDegrees(self):
		if self.geo_unit_derived!=ANGULAR_UNIT_DEGREES:
			self.geo_unit_derived=ANGULAR_UNIT_DEGREES
			self.translateDerivedGeoUnits()
		self.action_angular_units_derived[ANGULAR_UNIT_DEGREES].setChecked(True)
	def setDerivedAngularUnitsRadians(self):
		if self.geo_unit_derived!=ANGULAR_UNIT_RADIANS:
			self.geo_unit_derived=ANGULAR_UNIT_RADIANS
			self.translateDerivedGeoUnits()
		self.action_angular_units_derived[ANGULAR_UNIT_RADIANS].setChecked(True)
	def setDerivedAngularUnitsNt(self):
		if self.geo_unit_derived!=ANGULAR_UNIT_NT:
			self.geo_unit_derived=ANGULAR_UNIT_NT
			self.translateDerivedGeoUnits()
		self.action_angular_units_derived[ANGULAR_UNIT_NT].setChecked(True)
	def setDerivedAngularUnitsSx(self):
		if self.geo_unit_derived!=ANGULAR_UNIT_SX:
			self.geo_unit_derived=ANGULAR_UNIT_SX
			self.translateDerivedGeoUnits()
		self.action_angular_units_derived[ANGULAR_UNIT_SX].setChecked(True)
	def translateGeoUnits(self):
		if self.output_cache.is_valid and TrLib.IsGeographic(self.output_cache.mlb) :
			WidgetUtils.setOutput(self.output_cache.coords,self.output[:2],True,angular_unit=self.geo_unit,precision=self.coord_precision)
		if TrLib.IsGeographic(str(self.cb_input_system.currentText())):
			for field in self.input[:2]:
				WidgetUtils.translateAngularField(field,self.geo_unit)
		for widget in self.getAdditionalWidgets():
			if hasattr(widget,"handleGeoUnitChange"):
				widget.handleGeoUnitChange(self.geo_unit)
		for key in self.action_angular_units.keys():
			self.action_angular_units[key].setChecked(self.geo_unit==key)
		
	def translateDerivedGeoUnits(self):
		#for field in self.derived_angular_output:
		#	WidgetUtils.translateAngularField(field,self.geo_unit_derived)
		self.onShowScale()
		for widget in self.getAdditionalWidgets():
			if hasattr(widget,"handleAngularUnitChange"):
				widget.handleAngularUnitChange(self.geo_unit_derived)
		for key in self.action_angular_units_derived.keys():
			self.action_angular_units_derived[key].setChecked(self.geo_unit_derived==key)	
	#will be called both from event handler and programtically to set/clear fields on success/error#
	#Added numeric hack for s34, kk and os systems....
	def onShowScale(self):
		if (self.chb_show_scale.isChecked() and self.output_cache.is_valid):
			if not self.output_cache.has_scale:
				#cache scale and convergence....
				if (self.output_cache.proj_weakly_defined):
					if (self.output_cache.mlb!=self.numeric_scale_transf.mlb_in):
						self.numeric_scale_transf.Insert(self.output_cache.mlb,True)
					sc,m=getNumericScale(self.output_cache.coords[0],self.output_cache.coords[1],self.numeric_scale_transf,self.fallback_ellipsoid[1],self.fallback_ellipsoid[2])
					self.logInteractive("INFO: calculating scale and convergence numerically relative to ETRS89 datum","blue")
				else:
					sc,m=self.coordinate_transformation.GetLocalGeometry(self.output_cache.coords[0],self.output_cache.coords[1])
				self.output_cache.scale=sc
				self.output_cache.meridian_convergence=m
				self.output_cache.has_scale=True
			self.txt_scale.setText("%.7f" %self.output_cache.scale)
			self.txt_meridian_convergence.setText(translateFromDegrees(self.output_cache.meridian_convergence,self.geo_unit_derived,precision=0))
			if DEBUG:
				self.logInteractive(repr(self.output_cache.coords)+"\n"+self.output_cache.mlb)
		else:
			self.txt_scale.setText("")
			self.txt_meridian_convergence.setText("")
	
	def getInteractiveInput(self,mlb_in=None):
		if mlb_in is None:
			mlb_in=str(self.cb_input_system.currentText())
		is_angle=TrLib.IsGeographic(mlb_in)
		coords,msg=WidgetUtils.getInput(self.input,is_angle,angular_unit=self.geo_unit)
		if len(msg)>0:
			self.logInteractive(msg)
		return coords
	
	def setInteractiveOutput(self,coords,mlb_out=None):
		#if coords==[] we clear output fields#
		if mlb_out is None:
			mlb_out=str(self.cb_output_system.currentText())
		mlb_out=str(self.cb_output_system.currentText())
		is_angle=TrLib.IsGeographic(mlb_out)
		WidgetUtils.setOutput(coords,self.output,is_angle,z_fields=[2],angular_unit=self.geo_unit,precision=self.coord_precision)
		
		
		
	def setInteractiveInput(self,coords,mlb_in=None):
		if mlb_in is None:
			mlb_in=str(self.cb_input_system.currentText())
		is_angle=TrLib.IsGeographic(mlb_in)
		WidgetUtils.setOutput(coords,self.input,is_angle,z_fields=[2],angular_unit=self.geo_unit,precision=self.coord_precision)
		
		
	def transformInput(self,input_index_changed=False,output_index_changed=False):
		if self._clear_log:
			self.logInteractive("",clear=True)
		self.output_cache.is_valid=False
		self.output_cache.has_scale=False
		mlb_in=str(self.cb_input_system.currentText())
		mlb_out=str(self.cb_output_system.currentText())
		#self.logInteractive(repr(self.output_cache.coords))
		#Check if we should update system info
		update_in=(mlb_in!=self.mlb_in)
		update_out=(mlb_out!=self.output_cache.mlb)
		if ( update_in or update_out):
			self.setSystemInfo(update_in,update_out)
			self.mlb_in=mlb_in
			self.output_cache.mlb=mlb_out
			self.output_cache.proj_weakly_defined=Minilabel.isProjWeaklyDefined(mlb_out)
		coords=self.getInteractiveInput(mlb_in)
		if len(coords)!=3:
			self.logInteractive("Input coordinate in field %d not OK!" %(len(coords)+1),"red")
			self.setInteractiveOutput([])
			self.onShowScale()
			self.input[len(coords)].setFocus()
			return
		x_in,y_in,z_in=coords
		#Apply affine mod first.
		if self.affine_modifications.apply_interactive and self.affine_modifications.input.apply:
			x_in,y_in,z_in=self.affine_modifications.input.transform(x_in,y_in,z_in)
			self.logInteractive("Applying affine modification of input. Modified input: {0:.3f} {1:.3f} {2:.3f}".format(x_in,y_in,z_in),"blue")
		if  mlb_in!=self.coordinate_transformation.mlb_in: 
			try:
				self.coordinate_transformation.Insert(mlb_in)
			except Exception,msg:
				#if call was from in_system_changed - remove item
				if input_index_changed:
					self._handle_system_change=False
					self.cb_input_system.removeItem(self.cb_input_system.currentIndex())
					self.cb_input_system.setEditText(mlb_in)
					self._handle_system_change=True
				self.setInteractiveOutput([])
				self.logInteractive("Input label not OK!\n%s" %repr(msg),color="red")
				return
		#at this point mbl in and input coords are validated and we can attempt to draw the map point
		self.drawPoint(x_in,y_in,z_in,mlb_in)
		if mlb_out!=self.coordinate_transformation.mlb_out:	
			try:
				self.coordinate_transformation.Insert(mlb_out,False)
			except Exception,msg:
				if output_index_changed:
					self._handle_system_change=False
					self.cb_output_system.removeItem(self.cb_output_system.currentIndex())
					self.cb_output_system.setEditText(mlb_out)
					self._handle_system_change=True
				self.setInteractiveOutput([])
				self.logInteractive("Output label not OK!\n%s" %repr(msg),color="red")
				return
		try:
			x,y,z,h=self.coordinate_transformation.TransformGH(x_in,y_in,z_in)
		except Exception,msg:
			self.setInteractiveOutput([])
			err=TrLib.GetLastError()
			if err in ERRORS:
				self.logInteractive("%s" %ERRORS[err],color="red")
			else:
				self.logInteractive("Error in transformation",color="red")
			self.onShowScale()
			return
		#Cache output after succesfull transformation#
		self.output_cache.is_valid=True
		self.output_cache.coords=[x,y,z]
		self.onShowScale()#here we cache scale ond convergence also!
		self.txt_geoid_height.setText("%.4f m" %h)
		geoid_name=self.coordinate_transformation.GetGeoidName()
		if DEBUG:
			self.logInteractive("Geoid: %s" %geoid_name)
		#the affine modification should not infect scale, caching etc. - only used in display.
		if self.affine_modifications.apply_interactive and self.affine_modifications.output.apply:
			#check when in the logical chain to apply this.....
			x,y,z=self.affine_modifications.output.transform(x,y,z)
			self.logInteractive("Applying affine modification of output.","blue")
		#self.logInteractive(repr(self.output_cache.coords))
		self.setInteractiveOutput([x,y,z]) #does nothing but display the coords
		self.txt_geoid_name.setText(geoid_name)
		
	#TAB  File2File#
	def initF2FTab(self):
		#Auto completion - dont do it for now as input might not be a *file*
		#completer=QCompleter()
		#completer.setModel(QDirModel(completer))
		#completer.setCompletionMode(QCompleter.InlineCompletion)
		#self.txt_f2f_input_file.setCompleter(completer)
		if self.gdal_settings.load_mode==1:
			self.logF2F("Using included GDAL installation.")
		elif self.gdal_settings.load_mode==2:
			self.logF2F("Using custom GDAL installation.")
		else:
			self.logF2F("Using system GDAL installation.")
		frmts=LibTrui.getOGRFormats()
		self.cb_f2f_ogr_driver.clear()
		self.cb_f2f_ogr_driver.addItems(frmts)
		File2File.SetCommand(TROGR)
		rc,msg=File2File.TestCommand()
		if (rc!=0):
			self.message("Batch transformation program %s not availabe!" %TROGR)
			self.tab_ogr.setEnabled(False)
		self.logF2F(msg)
	
	
	def loadLibtrui(self):
		self.has_ogr,msg=LibTrui.initLibrary(BIN_PREFIX)
		if not self.has_ogr:
			dmsg="Unable to load c extension library, libtrui: "+msg
			dmsg+="\nA proper GDAL installation might not be present?\nConsider changing your GDAL settings from the 'Settings' menu."
			self.message(dmsg)
			self.tab_ogr.setEnabled(False)
			return
		LibTrui.setMessageHandler(lordCallback)
		self.initF2FTab()
		#decide if a mapthread should be started#
		self.mapthread=MapThread(self)
		self.mapthread.start() #and perhaps in the 'finished event handler we should zoom to the point??
		
	def onRdobtOGRToggled(self):
		checked=self.rdobt_f2f_ogr.isChecked()
		self.cb_f2f_ogr_driver.setEnabled(checked)
		self.bt_f2f_creation_options.setEnabled(checked)
		self.chb_f2f_all_layers.setEnabled(checked)
		if (not checked):
			self.chb_f2f_all_layers.setChecked(True)
		else:
			self.logF2F("Note: If your vector datasource is not 3-dimensional you should toglle off height in your input and output systems.","blue")
			
			
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_execute_clicked(self):
		self.transformFile2File()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_view_output_clicked(self):
		#TODO: Improve
		if not (self.f2f_settings.is_started and self.f2f_settings.is_done):
			self.message("No valid output - yet!")
			return
		if not self.f2f_settings.driver in ["KMS","TEXT"]:
			self.message("Use a dedicated viewer for GIS-files.")
			return
		ok=True
		if len(self.f2f_settings.output_files)>1:
			fname,ok=QInputDialog.getItem(self, "Ouput files", "Select a file to view", self.f2f_settings.output_files,False)
		else:
			fname=self.f2f_settings.output_files[0]
		if ok:
			fname=unicode(fname)
			dlg=TextViewer(self,fname=fname)
			dlg.exec_()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_view_log_clicked(self):
		if not (self.f2f_settings.is_started and self.f2f_settings.is_done):
			self.message("No valid output - yet!")
			return
		if self.f2f_settings.log_file is None:
			self.message("Log file not used....")
			return
		fname=self.f2f_settings.log_file
		dlg=TextViewer(self,fname=fname)
		dlg.exec_()
	#Event handlers for various buttons in f2f-tab#
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_change_h_in_clicked(self):
		mlb_in=str(self.cb_f2f_input_system.currentText())
		mlb=Minilabel.changeHeightSystem(mlb_in,H_SYSTEMS[self.region],DATUM_ALLOWED_H_SYSTEMS)
		if mlb!=mlb_in:
			self.cb_f2f_input_system.setEditText(mlb)
			self.onF2FSystemInChanged()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_change_h_out_clicked(self):
		mlb_out=str(self.cb_f2f_output_system.currentText())
		mlb=Minilabel.changeHeightSystem(mlb_out,H_SYSTEMS[self.region],DATUM_ALLOWED_H_SYSTEMS)
		if mlb!=mlb_out:
			self.cb_f2f_output_system.setEditText(mlb)
			self.onF2FSystemOutChanged()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_browse_input_clicked(self):
		my_file = QFileDialog.getOpenFileName(self, "Select a vector-data input file",self.dir)
		if len(my_file)>0:
			self.txt_f2f_input_file.setText(my_file)
			self.dir=os.path.dirname(unicode(my_file))
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_browse_input_dir_clicked(self):
		my_file = QFileDialog.getExistingDirectory(self, "Select an input directory",self.dir)
		if len(my_file)>0:
			self.txt_f2f_input_file.setText(my_file)
			self.dir=os.path.dirname(unicode(my_file))
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_browse_output_clicked(self):
		my_file = QFileDialog.getSaveFileName(self, "Select a vector-data output file",self.dir)
		if len(my_file)>0:
			self.txt_f2f_output_file.setText(my_file)
			self.dir=os.path.dirname(unicode(my_file))
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_browse_output_dir_clicked(self):
		my_file = QFileDialog.getExistingDirectory(self, "Select an output directory",self.dir)
		if len(my_file)>0:
			self.txt_f2f_output_file.setText(my_file)
			self.dir=os.path.dirname(unicode(my_file))
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_browse_log_clicked(self):
		my_file = QFileDialog.getSaveFileName(self, "Select a log file",self.dir)
		if len(my_file)>0:
			self.txt_f2f_log_name.setText(my_file)
			self.dir=os.path.dirname(unicode(my_file))
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_input_layers_clicked(self):
		inname=unicode(self.txt_f2f_input_file.text())
		if len(inname)>0:
			ds=LibTrui.open(inname.encode(sys.getfilesystemencoding())) #do encoding here? depends on what GDAL-bindings does.
			if ds is not None:
				layers=LibTrui.getLayerNames(ds)
				LibTrui.close(ds)
				dlg=LayerSelector(self,layers,self.txt_f2f_layers_in)
				dlg.exec_()
			else:
				self.message("Failed to open %s" %inname)
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_creation_options_clicked(self):
		drv=str(self.cb_f2f_ogr_driver.currentText())
		dlg=DialogCreationOptions(self,drv,LibTrui.OGR_LONG_TO_SHORT)
		dlg.exec_()
	
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_list_formats_clicked(self):
		text=File2File.ListFormats()
		self.logF2F(text,"blue")
	def onF2FSystemInChanged(self):
		if self.chb_f2f_label_in_file.isChecked():
			text="metadata in source"
		else:
			mlb_in=str(self.cb_f2f_input_system.currentText())
			text=TrLib.DescribeLabel(mlb_in)
			if self.affine_modifications.apply_f2f and self.affine_modifications.input.apply:
				text+=",+affine modification"
		self.lbl_f2f_input_info.setText("Input system info: %s" %text)
	def onF2FSystemOutChanged(self):
		mlb_out=str(self.cb_f2f_output_system.currentText())
		text=TrLib.DescribeLabel(mlb_out)
		if self.affine_modifications.apply_f2f and self.affine_modifications.output.apply:
				text+=",+affine modification"
		self.lbl_f2f_output_info.setText("Output system info: %s" %text)
	def setupAffine(self):
		#setup params for affine transformation...
		dlg=DialogSetupAffine(self,self.affine_modifications)
		r=dlg.exec_()
		if r==QDialog.Accepted:
			#I guess we should trigger a transformation if there are changes
			#we probably have changes in affine modifications - but perhaps not in any mlbs. 
			#Set system info is only called in interactive tab on changes in real systems.
			self.setSystemInfo(True,True)
			self.onF2FSystemOutChanged()
			self.onF2FSystemInChanged()
			#trigger a retransformation
			if self.affine_modifications.apply_interactive:
				self.transformInput() #system info is already set.
		#do something here...
	def transformFile2File(self):
		file_in=unicode(self.txt_f2f_input_file.text())
		file_out=unicode(self.txt_f2f_output_file.text())
		self.f2f_settings.is_started=False
		if len(file_in)==0:
			self.message("Set input datasource!")
			self.txt_f2f_input_file.setFocus()
			return
		if len(file_out)==0:
			self.message("Set output datasource!")
			self.txt_f2f_output_file.setFocus()
			return
		if file_in==file_out:
			self.message("Input and output files must differ (for now)")
			return
		if file_in[-1] in ["/","\\"]:
			file_in=file_in[:-1]
		if file_out[-1] in ["/","\\"]:
			file_out=file_out[:-1]
		mlb_in=str(self.cb_f2f_input_system.currentText())
		mlb_out=str(self.cb_f2f_output_system.currentText())
		#Just do this - in case it hasn't been done already!
		self.onF2FSystemInChanged()
		self.onF2FSystemOutChanged()
		if len(mlb_out)==0:
			self.message("Output system label must be specified!")
			return
		#clear the log#
		self.txt_f2f_log.clear()
		if self.rdobt_f2f_ogr.isChecked():
			drv=str(self.cb_f2f_ogr_driver.currentText())
			self.f2f_settings.format_out=drv
			self.f2f_settings.driver="OGR"
		elif self.rdobt_f2f_simple_text.isChecked():
			self.f2f_settings.driver="TEXT"
		elif self.rdobt_f2f_dsfl.isChecked():
			self.f2f_settings.driver="DSFL"
		else:
			self.f2f_settings.driver="KMS"
		if self.chb_f2f_use_log.isChecked():
			log_name=unicode(self.txt_f2f_log_name.text())
			if len(log_name)==0:
				self.message("Specify log file name.")
				return
			self.f2f_settings.be_verbose=self.chb_f2f_verbose.isChecked()
		else:
			log_name=None
			self.f2f_settings.be_verbose=False
		#encode filenames in file system encoding since we need to pass on to another executable - done just in time in File2File#
		self.f2f_settings.log_file=log_name
		self.f2f_settings.ds_in=file_in
		self.f2f_settings.ds_out=file_out
		self.f2f_settings.mlb_out=mlb_out
		self.f2f_settings.set_projection=self.chb_f2f_set_projection.isChecked()
		if (not self.chb_f2f_all_layers.isChecked()) and self.f2f_settings.driver=="OGR":
			_layers=str(self.txt_f2f_layers_in.text()).split(";")
			layers=[]
			for layer in _layers:
				if len(layer)>0:
					layers.append(layer.strip())
			self.f2f_settings.input_layers=layers
		else:
			self.f2f_settings.input_layers=[]
		if not self.chb_f2f_label_in_file.isChecked():
			self.f2f_settings.mlb_in=mlb_in
		else:
			self.f2f_settings.mlb_in=None
		if self.affine_modifications.apply_f2f:#affine mod not implemented for DSFL
			if self.f2f_settings.driver!="DSFL": 
				self.f2f_settings.affine_mod_in=self.affine_modifications.input
				self.f2f_settings.affine_mod_out=self.affine_modifications.output
			else:
				self.log_f2f("Note: Affine modifications not supported for DSFL-formate","orange")
		else:
			self.f2f_settings.affine_mod_in=None
			self.f2f_settings.affine_mod_out=None
			
		ok,msg=File2File.transformDatasource(self.f2f_settings,self.message_poster.postFileMessage,self.message_poster.postReturnCode)
		if not ok:
			self.message(msg)
		else:
			#we're running#
			self.f2f_settings.is_started=True
			self.f2f_settings.is_done=False
			self.bt_f2f_execute.setEnabled(False)
			self.bt_f2f_view_output.setEnabled(False)
			self.bt_f2f_view_log.setEnabled(False)
			self.bt_f2f_kill.setEnabled(True)
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_kill_clicked(self):
		self.killBatchProcess()
	def killBatchProcess(self):
		self.logF2F("Sending kill signal...")
		File2File.KillThreads()
	def onF2FReturnCode(self,rc):
		if rc==TrLib.TR_OK:
			self.logF2F("....done....")
		elif rc==File2File.PROCESS_TERMINATED:
			self.logF2F("Process was terminated!")
		else:
			self.message("Errors occured during transformation - see log field.")
		#we're running - a method terminating the process could also enable buttons... and probably will#
		self.f2f_settings.is_done=True
		self.bt_f2f_execute.setEnabled(True)
		self.bt_f2f_view_output.setEnabled(True)
		self.bt_f2f_view_log.setEnabled(True)
		self.bt_f2f_kill.setEnabled(False)
	
	
	
	#MESSAGE AND LOG METHODS#
	def logInteractive(self,text,color="black",clear=False):
		self.txt_log.setTextColor(QColor(color))
		if clear:
			self.txt_log.setText(text)
		else:
			self.txt_log.append(text)
		self.txt_log.ensureCursorVisible()
	def logInteractiveStdout(self,text):
		self.logInteractive(text,"green")
	def logInteractiveStderr(self,text):
		self.logInteractive(text,"red")
	def logInteractiveCallBack(self,text):
		self.logInteractive(text,"blue")
	def logF2F(self,text,color="black",insert=False):
		self.txt_f2f_log.setTextColor(QColor(color))
		if insert:
			self.txt_f2f_log.insertPlainText(text)
		else:
			self.txt_f2f_log.append(text)
		self.txt_f2f_log.ensureCursorVisible()
	
	def logF2Fstdout(self,text):
		self.logF2F(text,"green")
	def logF2FStderr(self,text):
		self.logF2F(text,"red")
	def logF2FCallback(self,text):
		self.logF2F(text,"blue")
	
	def message(self,text,title="Error"):
		QMessageBox.warning(self,title,text)
	
	def displayCallbackMessage(self,text):
		#check if current widget handles call_back
		widget=self.main_tab_host.currentWidget()
		if hasattr(widget,"handleCallBack"):
			widget.handleCallBack(text)
		else:
			self.message(text)
	def handleStdOut(self,text):
		widget=self.main_tab_host.currentWidget()
		if hasattr(widget,"handleStdOut"):
			widget.handleStdOut(text)
	def handleStdErr(self,text):
		widget=self.main_tab_host.currentWidget()
		if hasattr(widget,"handleStdErr"):
			widget.handleStdErr(text)
	#SETTINGS#
	def saveSettings(self):
		if not self._save_settings:
			return
		settings = QSettings(COMPANY_NAME,PROG_NAME)
		settings.beginGroup('MainWindow')
		settings.setValue('size', self.size())
		settings.setValue('position', self.pos())
		settings.endGroup()
		settings.beginGroup('gdal')
		settings.setValue('load_mode',self.gdal_settings.load_mode)
		settings.setValue('bin_path',self.gdal_settings.paths[0])
		settings.setValue('data_path',self.gdal_settings.paths[1])
		settings.setValue('plugin_path',self.gdal_settings.paths[2])
		settings.endGroup()
		settings.beginGroup('plugins')
		settings.setValue('enable',int(self.enable_plugins))
		settings.endGroup()
		settings.beginGroup('data')
		settings.setValue('geoids',self.geoids)
		settings.setValue('path',self.dir)
		settings.setValue('script_path',self.script_dir)
		settings.setValue('region',self.region)
		settings.endGroup()
	def loadSettings(self):
		#We catch exceptions here - otherwise the window wont show and it can be hard for py2exe users to find out
		#that they have to locate and view the log file...
		caught=""
		settings = QSettings(COMPANY_NAME,PROG_NAME)
		settings.beginGroup('MainWindow')
		self.resize(settings.value('size', self.size()).toSize())
		self.move(settings.value('position', self.pos()).toPoint())
		settings.endGroup()
		self.gdal_settings=GDALSettings()
		if not IS_WINDOWS:
			self.gdal_settings.load_mode=0  #Standard mode for all but windows
		else:
			settings.beginGroup('gdal')
			self.gdal_settings.load_mode,ok=settings.value('load_mode',1).toInt()
			paths=[]
			for key in ['bin_path','data_path','plugin_path']:
				try:
					paths.append(unicode(settings.value(key,"").toString()))
				except Exception,e:
					paths.append("")
					caught+="GDAL-settings,caught: %s\n" %str(e)
			self.gdal_settings.paths=paths
			if DEBUG:
				self.message("%s" %(repr(self.gdal_settings.__dict__)))
			settings.endGroup()
		settings.beginGroup('plugins')
		enable_plugins,ok=settings.value('enable',1).toInt()
		if ok:
			self.enable_plugins=bool(enable_plugins)
		else:
			self.enable_plugins=True
		settings.endGroup()
		settings.beginGroup('data')
		#geoids=settings.value('geoids')
		#if geoids.isValid():
		#	try:
		#		self.geoids=unicode(geoids.toString())
		#	except:
		#		caught+="Encoding error for stored geoid dir.\n"
		#		self.geoids=None
		#else:
		#	self.geoids=None
		dir=settings.value('path',DEFAULT_DIR)
		try:
			self.dir=unicode(dir.toString())
		except Exception,e:
			self.dir=DEFAULT_DIR
			caught+="Path-settings,caught: %s\n" %str(e)
		dir=settings.value('script_path',self.dir)
		try:
			self.script_dir=unicode(dir.toString())
		except Exception,e:
			self.script_dir=self.dir
			caught+="Path-settings,caught: %s\n" %str(e)
		try:
			region=unicode(settings.value('region',REGION_DK).toString())
		except:
			region=REGION_DK
		if not region in REGIONS:
			region=REGION_DK
		self.region=region
		settings.endGroup()
		if len(caught)>0:
			self.message("Errors during loadSettings:\n%s" %caught)
	def selectTabDir(self):
		my_file = unicode(QFileDialog.getExistingDirectory(self, "Select a valid geoid directory",self.dir))
		return my_file
	
	def changeTabDir(self):
		my_file = self.selectTabDir()
		if len(my_file)>0:
			self.closeTransformations()
			ok,msg=TrLib.SetGeoidDir(my_file)
			if ok:
				self.lbl_geoid_dir_value.setText(os.path.realpath(my_file))
				self.geoids=my_file
				os.environ["TR_TABDIR"]=self.geoids.encode(sys.getfilesystemencoding())
				self.saveSettings()
			else:
				TrLib.SetGeoidDir(self.geoids)
				self.message("Failed to change geoid dir!\n%s" %msg)
			self.initTransformations()
	#PLUGINS#
	def togglePluginsEnabled(self):
		self.enable_plugins= not self.enable_plugins
		if self.enable_plugins:
			state="enabled"
			self.actionPlugins_enabled.setText("Disable plugins")
		else:
			state="disabled"
			self.actionPlugins_enabled.setText("Enable plugins")
		self.saveSettings()
		QMessageBox.information(self,"Plugins "+state ,"Changes will take effect after a restart.")
	#PLUGIN LOADER#
	def loadPlugins(self):
		plugins,dublicates=getPlugins([PLUGIN_PATH_USER,PLUGIN_PATH_LOCAL])
		if len(plugins)>0:
			if not HAS_IMPORTLIB:
				self.logInteractive("Plugin loader needs importlib (python version>=2.7)",color="red")
				return
			if not PLUGIN_PATH_LOCAL in sys.path:
				sys.path.insert(0,PLUGIN_PATH_LOCAL)
			if not PLUGIN_PATH_USER in sys.path:
				sys.path.insert(0,PLUGIN_PATH_USER)
			if len(dublicates)>0:
				self.logInteractive("Dublicate plugin modules:\n%s\nModules defined in user directory will have precedence." %repr(dublicates),"brown")
			for plugin in plugins:
				self.logInteractive("Loading plugin: %s" %plugin,color="brown")
				try:
					_plugin=importlib.import_module(plugin)
				except Exception,msg:
					print repr(msg)
				else:
					#Test if this is a widget type plugin!
					if hasattr(_plugin,"getWidget"):
						self.addPluginWidget(_plugin)
					if hasattr(self,"tab_python") and hasattr(self.tab_python,"addModule"):
						self.tab_python.addModule(_plugin,plugin)
					if hasattr(_plugin,"startPlugin"):
						_plugin.startPlugin(self)
		else:
			self.logInteractive("No python plugins found...")
	#Add TAB - for widget type plugins#
	def addPluginWidget(self,plugin):
		#TODO: implement a manager, which allows enabling/disabling plugins - which means that we should store info 
		#on loaded plugins and tab positions....
		if hasattr(plugin,"getName"):
			name=plugin.getName()
		else:
			name="some_plugin"
		self.logInteractive("Widget type plugin - added as tab: %s" %name,color="brown")
		widget=plugin.getWidget(self)
		self.main_tab_host.addTab(widget,name)
	def getAdditionalWidgets(self):
		count=self.main_tab_host.count()
		if count>2:
			widgets=[self.main_tab_host.widget(i) for i in range(2,count)]
			return widgets
		return []
	#ON CLOSE - SAVE SETTINGS#
	def closeEvent(self, event):
		self.saveSettings()
		QMainWindow.closeEvent(self, event)
		

def main():
	global app
	app = QtGui.QApplication(sys.argv)
	launcher=LauncherWindow()
	sys.exit(app.exec_())

if __name__=="__main__":
	main()
	
	
		
