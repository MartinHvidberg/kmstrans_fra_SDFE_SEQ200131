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
from PyQt4 import QtCore, QtGui
try:
	from PyQt4 import Qsci
except:
	HAS_QSCI=False
else:
	HAS_QSCI=True
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from Main_gui import Ui_GSTtrans
from Dialog_settings_f2f import Ui_Dialog as Ui_Dialog_f2f
from Dialog_layer_selector import Ui_Dialog as Ui_Dialog_layer_selector
import Minilabel
import TrLib
from TrLib_constants import *
import threading, subprocess
import File2File
import sys,os,time
import EmbedPython
try:
	import importlib
except ImportError:
	HAS_IMPORTLIB=False
else:
	HAS_IMPORTLIB=True

DEBUG="-debug" in sys.argv
OVERRIDE_LOCAL_GDAL="-my_gdal" in sys.argv
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
PROG_NAME="trui"
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
PLUGIN_PATH=os.path.expanduser(os.path.join("~","."+PROG_NAME,"plugins"))
if not os.path.exists(PLUGIN_PATH):
	try:
		os.makedirs(PLUGIN_PATH)
	except:
		pass
DOC_PATH="file://"+PREFIX+"/"+"doc"
#POINTER TO WEB PAGES
URL_HELP_LOCAL=DOC_PATH+"/index.html"
#SET UP ENVIRONMENT#
#Set up local GDAL env#
IS_LOCAL_GDAL=False
if (os.path.exists(GDAL_PREFIX)) and (not OVERRIDE_LOCAL_GDAL) and IS_WINDOWS:
	if os.path.exists(GDAL_DATA_PATH):
		os.environ["GDAL_DATA"]=GDAL_DATA_PATH
	if os.path.exists(GDAL_PLUGIN_PATH):
		os.environ["GDAL_DRIVER_PATH"]=GDAL_PLUGIN_PATH
	if os.path.exists(GDAL_BIN_PATH):
		env=os.environ["PATH"]
		os.environ["PATH"]=GDAL_BIN_PATH+os.pathsep+env
	IS_LOCAL_GDAL=True
	
#MAKE SURE THAT THE LIBRARIES ARE FINDABLE ON LINUX/MAC - THEY SEEM TO AUTOMATICALLY BE AS LONG AS LOCATED NEXT TO EXECUTABLE...
#END SETUP ENV#


#DEFAULT DIR FOR FILE BROWSING - COULD BE STORED IN INI-FILE#
if "HOME" in os.environ:
	DEFAULT_DIR=os.environ["HOME"]
elif "HOMEPATH" in os.environ:
	DEFAULT_DIR=os.environ["HOMEPATH"]
else:
	DEFAULT_DIR="/"

#DEFAULT FIELD LABELING MECHANISM#
GEO_LABELS=["Longitude:","Latitude:","H:"]
PROJ_LABELS=["Easting:","Northing:","H:"]
CRT_LABELS=["X:","Y:","Z:"]
SYSTEM_LABELS={Minilabel.CRT_CODE:CRT_LABELS,Minilabel.PROJ_CODE:PROJ_LABELS,Minilabel.GEO_CODE:GEO_LABELS}



VERSION="TRUI b1.0 (UI for TrLib demo)"

#SOME DEFAULT TEXT VALUES
ABOUT=VERSION+"""
\nWritten in PyQt4. Report bugs to simlk@gst.dk.
"""

#Custom events and threads# 
RENDER_COMPLETE=1234 #must be in betweeen MIN_USER and MAX_USER
FILE_LOG_EVENT=1235
RETURN_CODE_EVENT=1236

class MapEvent(QEvent):
	def __init__(self,type=RENDER_COMPLETE):
		QEvent.__init__(self,type)

class FileLogEvent(QEvent):
	def __init__(self,msg,type=FILE_LOG_EVENT):
		QEvent.__init__(self,type)
		self.msg=msg

class ReturnCodeEvent(QEvent):
	def __init__(self,rc,type=RETURN_CODE_EVENT):
		QEvent.__init__(self,type)
		self.rc=rc
		
class MessagePoster(object):
	def __init__(self,win):
		self.win=win
	def PostFileMessage(self,text):
		event=FileLogEvent(text)
		app.postEvent(self.win,event)
	def PostReturnCode(self,rc):
		event=ReturnCodeEvent(rc)
		app.postEvent(self.win,event)
		

class MapThread(threading.Thread):
	def __init__(self,win,region=REGION_DK):
		threading.Thread.__init__(self)
		self.win=win
		self.region=region #not used at the moment - for selecting coastline according to region....
	def run(self):
		t1=time.clock()
		lines=File2File.GetLines(COAST_PATH)
		self.paths=[]
		for line in lines:
			path=QPainterPath(QPointF(line[0][0],-line[0][1]))
			for i in range(1,len(line)):
				path.lineTo(line[i][0],-line[i][1])
			self.paths.append(path)
		t2=time.clock()
		app.postEvent(self.win,MapEvent(RENDER_COMPLETE))


#Very very simple callback handling messages from TrLib# 
def LordCallback(err_class,err_code,msg):
	try:
		MainWindow.displayCallbackMessage(msg.strip())
	except:
		pass

#Get a list of plugins
def GetPlugins(path):
	if not os.path.exists(path):
		return []
	files=os.listdir(path)
	plugins=[]
	for name in files:
		location=os.path.join(path,name)
		if os.path.isdir(location):
			plugins.append(os.path.basename(name))
	return plugins

#A class to keep cached output data#
class PointData(object):
	def __init__(self):
		self.is_valid=False
		self.coords=None
		self.mlb=None
		self.meridian_convergence=None
		self.scale=None
	
class BesselHelmertCache(object):
	def __init__(self):
		self.mlb=None
		self.input_coords=[]
		self.geo_coords=[]
		self.azimuths=[]
		self.distance=None


class DialogFile2FileSettings(QtGui.QDialog,Ui_Dialog_f2f):
	"""Class for specifying options to TEXT and KMS drivers"""
	def __init__(self,parent,settings):
		QtGui.QDialog.__init__(self,parent)
		self.setupUi(self)
		self.settings=settings
		self.settings.accepted=False
	#TODO: implement save and load settings like in MainWindow - should also *always* display the current settings, so that the cancel button should uncheck/recheck stuff.
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_close_clicked(self):
		ok=self.apply()
		if ok:
			self.hide()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_apply_clicked(self):
		self.apply()
	def apply(self):
		col_x=self.spb_col_x.value()
		col_y=self.spb_col_y.value()
		if self.chb_has_z.isChecked():
			col_z=self.spb_col_z.value()
		else:
			col_z=None
		if  col_x==col_y or col_x==col_z or col_y==col_x:
			self.message("Geometry columns must differ!")
			return False
		sep_char=""
		if self.chb_whitespace.isChecked():
			sep_char=None
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
		#else get the stuff from other boxes...#
		self.settings.col_x=col_x
		self.settings.col_y=col_y
		self.settings.col_z=col_z
		self.settings.sep_char=sep_char
		self.settings.accepted=True
		return True
	def message(self,text,title="Error"):
		QMessageBox.warning(self,title,text)

class TextViewer(QDialog):
	"""Class to display text files"""
	def __init__(self,parent,txt=None,fname=None):
		QDialog.__init__(self,parent)
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
			n=os.path.getsize(fname)
			if n==os.error:
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
		self.close()

	
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
		

	

class GSTtrans(QtGui.QMainWindow,Ui_GSTtrans):
	def __init__(self,parent=None):
		QtGui.QMainWindow.__init__(self,parent) 
		self.setupUi(self)
		#APPEARANCE#
		self.setWindowTitle(VERSION)
		#Set up event handlers#
		#some event handlers defined directly by special method names#
		self.cb_input_system.currentIndexChanged.connect(self.onSystemInChanged)
		self.cb_output_system.currentIndexChanged.connect(self.onSystemOutChanged)
		self.cb_bshlm_system.currentIndexChanged.connect(self.onBshlmSystemChanged)
		self.cb_f2f_input_system.currentIndexChanged.connect(self.onF2FSystemInChanged)
		self.cb_f2f_output_system.currentIndexChanged.connect(self.onF2FSystemOutChanged)
		self.chb_show_scale.clicked.connect(self.onShowScale)
		self.bt_python_run.clicked.connect(self.onPythonCommand)
		self.bt_f2f_settings.clicked.connect(self.openFile2FileSettings)
		#Menu event handlers#
		self.actionNew_KMSTrans.triggered.connect(self.onNewKMSTrans)
		self.actionExit.triggered.connect(self.onExit)
		self.actionAbout_KMSTrans.triggered.connect(self.onAbout)
		self.actionHelp_local.triggered.connect(self.onHelp_local)
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
		#end setup event handlers#
		
		#Set up convienient pointers to input and output#
		self.input=[self.txt_x_in,self.txt_y_in,self.txt_z_in]
		self.input_labels=[self.lbl_x_in,self.lbl_y_in,self.lbl_z_in]
		self.output=[self.txt_x_out,self.txt_y_out,self.txt_z_out]
		self.output_labels=[self.lbl_x_out,self.lbl_y_out,self.lbl_z_out]
		self.input_bshlm=[self.txt_bshlm_x1,self.txt_bshlm_y1,self.txt_bshlm_x2,self.txt_bshlm_y2]
		self.output_bshlm_geo=[self.txt_bshlm_lon1,self.txt_bshlm_lat1,self.txt_bshlm_lon2,self.txt_bshlm_lat2]
		self.output_bshlm_azimuth=[self.txt_bshlm_distance,self.txt_bshlm_azimuth1,self.txt_bshlm_azimuth2]
		self.input_bshlm_azimuth=self.output_bshlm_azimuth[:2]
		self.input_labels_bshlm=[self.lbl_bshlm_x,self.lbl_bshlm_y]
		self.derived_angular_output=[self.txt_meridian_convergence]+self.output_bshlm_azimuth[1:]
		self.action_angular_units={ANGULAR_UNIT_DEGREES:self.actionDegrees,ANGULAR_UNIT_RADIANS:self.actionRadians,
		ANGULAR_UNIT_SX:self.actionSx,ANGULAR_UNIT_NT:self.actionNt}
		self.action_angular_units_derived={ANGULAR_UNIT_DEGREES:self.actionDegrees_derived,ANGULAR_UNIT_RADIANS:self.actionRadians_derived,
		ANGULAR_UNIT_SX:self.actionSx_derived,ANGULAR_UNIT_NT:self.actionNt_derived}
		#SET UP INPUT EVENT HANDLERS: TRANSFORM ON RETURN. TODO: ADD VALIDATOR#
		for field in self.input:
			field.returnPressed.connect(self.transform_input)
		#END SETUP INPUT EVENT HANDLERS#
		#SETUP BSHLM EVENT HANDLERS#
		for field in self.input_bshlm+self.input_bshlm_azimuth:
			field.returnPressed.connect(self.doBesselHelmert)
		#Create Whatsthis in help menu#
		self.menuHelp.addSeparator()
		self.menuHelp.addAction(QWhatsThis.createAction(self))
		#SETUP VARIOUS ATTRIBUTES#
		self.message_poster=MessagePoster(self)
		self.f2f_settings=File2File.F2F_Settings()
		self.dialog_f2f_settings=DialogFile2FileSettings(self,self.f2f_settings)
		self.output_cache=PointData()
		self.geo_unit=ANGULAR_UNIT_DEGREES
		self.geo_unit_derived=ANGULAR_UNIT_DEGREES
		self.action_angular_units[self.geo_unit].setChecked(True)
		self.action_angular_units_derived[self.geo_unit_derived].setChecked(True)
		self.region=REGION_DK
		self._handle_system_change=True
		self.CoordinateTransformation=None
		self.HeightTransformation=None
		self.point_center=[0,0]
		self.map_zoom=0
		try:
			sys.frozen
		except:
			pass
		else:
			self.log_interactive("Running thorugh py2exe")
		#redirect python output#
		sys.stdout=RedirectOutput(self.log_pythonStdOut)
		#init TrLib and load settings#
		ok,msg=TrLib.LoadLibrary(TRLIB,BIN_PREFIX)
		TrLib.SetMessageHandler(LordCallback)
		if not ok:
			self.message("Failed to load transformation library: %s" %msg)
			self.close()
		ok=False
		self.loadSettings()
		if self.geoids is None and "TR_TABDIR" in os.environ:
			self.geoids=os.environ["TR_TABDIR"]
		while (not ok) or (self.geoids is None):
			if self.geoids is not None:
				try:
					ok=TrLib.InitLibrary(self.geoids,None,None)
				except Exception, e_value:
					self.message("Failed to initialise TrLib:\n%s" %(str(e_value)))
			if not ok:
				self.message("Geoid dir is not set - please select a valid geoid directory.")
				self.geoids=self.selectTabDir()
		TrLib.SetThreadMode(False)
		os.environ["TR_TABDIR"]=self.geoids
		#Will initialise some attributes which must be present in other methods#
		self.has_ogr=File2File.InitOGR(BIN_PREFIX)
		self.initF2FTab()
		self.drawMap()
		self.initRegion()
		self.lbl_geoid_dir_value.setText(os.path.realpath(self.geoids))
		#Setup for interactive python session. TODO: add some stuff to namespace#
		self.log_pythonStdOut("Python version:\n"+sys.version)
		namespace={"loadPlugins":self.loadPlugins,"mainWindow":self}
		self.log_pythonStdOut("Handle to main window %s stored in name: mainWindow" %repr(self.__class__),color="brown")
		self.python_console=EmbedPython.PythonConsole(namespace)
		self.python_console.ExecuteCode("from TrLib import *")
		self.loadPlugins()
		if HAS_QSCI:
			self.txt_python_in=Qsci.QsciScintilla(self.tab_python)
			self.txt_python_in.setLexer(Qsci.QsciLexerPython())
			self.txt_python_in.setAutoIndent(True)
		else:
			self.txt_python_in=QTextEdit(self.tab_python)
		self.tab_python.layout().addWidget(self.txt_python_in)
		self.txt_python_in.keyPressEvent=self.onPythonKey
		self.pythonExample()
		if not HAS_QSCI:
			self.log_pythonStdOut("Qscintilla not installed. Python input lexer will not work...")
		self.python_console.ClearCache()
		self.txt_python_in.setWhatsThis("Enter/edit input python code here") 
		#move to interactive tab
		try:
			self.tab_gsttrans.setCurrentIndex(0)
		except:
			pass
		#Setup tab indices dynamically - easier to maintain. Useful for displaying call back messages the right place#
		self.tabs=[self.tab_interactive,self.tab_ogr,self.tab_utilities,self.tab_python]
		self.tab_indices=[self.tab_gsttrans.indexOf(tab) for tab in self.tabs]
		self.log_methods=[self.log_interactive,self.log_f2f,self.log_bshlm,self.log_python]
		self.log_method_map=dict(zip(self.tab_indices,self.log_methods))
		#Only now - redirect python stderr - to be able to see errors in the initialisation#
		sys.stderr=RedirectOutput(self.log_pythonStdErr)
		
	def onExit(self):
		self.close()
	def onActionWhatsThis(self):
		QWhatsThis.enterWhatsThisMode()
	def onHelp_local(self):
		try:
			import webbrowser
			webbrowser.open(URL_HELP_LOCAL)
		except Exception,msg:
			self.message("Failed to help page in web browser:\n"+repr(msg))
	def onAbout(self):
		msg=ABOUT+"\nTransformation engine:\n%s"%TrLib.GetVersion()
		QMessageBox.about(self,"About "+PROG_NAME,msg)
	def openFile2FileSettings(self):
		self.dialog_f2f_settings.show()
	def onNewKMSTrans(self):
		subprocess.Popen([sys.executable,sys.argv[0]])
		self.log_interactive("Starting new process")
	#Map Stuff#	
	def drawMap(self):
		self.scene=QtGui.QGraphicsScene(self.gv_map)
		self.gv_map.setScene(self.scene)
		self.gv_map.setInteractive(True)
		self.gv_map.setDragMode(QGraphicsView.ScrollHandDrag)
		self.scene.setSceneRect(-180,-90,360,180)
		self.scene.addLine(-180,0,180,0)
		self.scene.addLine(0,90,0,-90)
		self.map_point=QtGui.QGraphicsEllipseItem(0,0,10,10)
		self.map_point.setBrush(QtGui.QBrush(QColor(255, 10, 10, 200)))
		if self.has_ogr:
			self.mapthread=MapThread(self)
			self.mapthread.start() #and perhaps in the 'finished event handler we should zoom to the point??
		else:
			self.scene.addItem(self.map_point)
	def customEvent(self,event):
		if int(event.type())==RENDER_COMPLETE:
			paths=self.mapthread.paths
			self.log_interactive("Load of coastline completed. Rendering...")
			t1=time.clock()
			for path in paths:
				self.scene.addPath(path)
			t2=time.clock()
			self.log_interactive("Render time: %.4f s" %(t2-t1))
			self.scene.addItem(self.map_point)
		if int(event.type())==FILE_LOG_EVENT:
			self.log_f2f(event.msg)
		if int(event.type())==RETURN_CODE_EVENT:
			self.onF2FReturnCode(event.rc)
			

	def drawPoint(self,x,y,mlb_in):
		self.map_transform=TrLib.CoordinateTransformation(mlb_in,"geo_wgs84")
		x,y,z=self.map_transform.Transform(x,y)
		r=2**(-self.map_zoom)*10
		self.map_point.setPos(x-r*0.5,-y-r*0.5)
		self.map_coords=(x,y)
		self.scene.update()
		self.map_transform.Close()
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
		self.cb_bshlm_system.clear()
		self.cb_f2f_input_system.addItems(systems)
		self.cb_f2f_output_system.addItems(systems)
		self.cb_input_system.addItems(systems)
		self.cb_output_system.addItems(systems)
		planar_systems=Minilabel.GetPlanarSystems(systems)
		self.cb_bshlm_system.addItems(planar_systems)
		self.setInteractiveInput(init_coords)
		self.cb_input_system.setCurrentIndex(0) #TODO: dont emit signal!
		self.cb_output_system.setCurrentIndex(0)
		self._handle_system_change=True
		self.setSystemInfo(True,True)
		self.transform_input() #this should trigger the redraw of the point
		self.zoomMap()
		
	def onSystemInChanged(self):
		if not self._handle_system_change:
			return
		self.setSystemInfo(True,False)
		#Trigger a transformation#
		self.transform_input()
		
	
	def onSystemOutChanged(self):
		if not self._handle_system_change:
			return
		self.setSystemInfo(False,True)
		#Trigger a transformation#
		self.transform_input()
		
			
	def setSystemInfo(self,do_input=True,do_output=False):
		if do_input:
			mlb_in=str(self.cb_input_system.currentText())
			text=self.GetDescription(mlb_in)
			self.lbl_input_info.setText("Input system info: %s" %text)
			sys_code_in=Minilabel.GetSysCode(mlb_in)
			if sys_code_in in SYSTEM_LABELS:
				labels=SYSTEM_LABELS[sys_code_in]
				for i in range(3):
					self.input_labels[i].setText(labels[i])
		if do_output:
			mlb_out=str(self.cb_output_system.currentText())
			text=self.GetDescription(mlb_out)
			self.lbl_output_info.setText("Output system info: %s" %text)
			
			sys_code_out=Minilabel.GetSysCode(mlb_out)
			
			if sys_code_out in SYSTEM_LABELS:
				labels=SYSTEM_LABELS[sys_code_out]
				for i in range(3):
					self.output_labels[i].setText(labels[i])
		
		
		
	def GetDescription(self,mlb):
		return TrLib.DescribeLabel(mlb)
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_change_h_in_clicked(self):
		mlb_in=str(self.cb_input_system.currentText())
		mlb=Minilabel.ChangeHeightSystem(mlb_in,H_SYSTEMS[self.region])
		if mlb!=mlb_in:
			self.cb_input_system.setEditText(mlb)
			self.onSystemInChanged()
		
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_change_h_out_clicked(self):
		mlb_out=str(self.cb_output_system.currentText())
		mlb=Minilabel.ChangeHeightSystem(mlb_out,H_SYSTEMS[self.region])
		if mlb!=mlb_out:
			self.cb_output_system.setEditText(mlb)
			self.transform_input()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_interactive_swap_clicked(self):
		#Transform - then swap input/output
		self.transform_input()
		if self.output_cache.is_valid:
			self._handle_system_change=False
			mlb_in=str(self.cb_input_system.currentText())
			mlb_out=self.output_cache.mlb
			in_vals=self.getInteractiveInput()
			self.setInteractiveInput(self.output_cache.coords,mlb_out)
			self.cb_input_system.setEditText(mlb_out)
			self.cb_output_system.setEditText(mlb_in)
			self._handle_system_change=True
			self.setSystemInfo(True,True)
			self.transform_input()
			
			
		
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
	def setAngularUnitsRadians(self):
		if self.geo_unit!=ANGULAR_UNIT_RADIANS:
			self.geo_unit=ANGULAR_UNIT_RADIANS
			self.translateGeoUnits()
	def setAngularUnitsNt(self):
		if self.geo_unit!=ANGULAR_UNIT_NT:
			self.geo_unit=ANGULAR_UNIT_NT
			self.translateGeoUnits()
	def setAngularUnitsSx(self):
		if self.geo_unit!=ANGULAR_UNIT_SX:
			self.geo_unit=ANGULAR_UNIT_SX
			self.translateGeoUnits()
	def setDerivedAngularUnitsDegrees(self):
		if self.geo_unit_derived!=ANGULAR_UNIT_DEGREES:
			self.geo_unit_derived=ANGULAR_UNIT_DEGREES
			self.translateDerivedGeoUnits()
	def setDerivedAngularUnitsRadians(self):
		if self.geo_unit_derived!=ANGULAR_UNIT_RADIANS:
			self.geo_unit_derived=ANGULAR_UNIT_RADIANS
			self.translateDerivedGeoUnits()
	def setDerivedAngularUnitsNt(self):
		if self.geo_unit_derived!=ANGULAR_UNIT_NT:
			self.geo_unit_derived=ANGULAR_UNIT_NT
			self.translateDerivedGeoUnits()
	def setDerivedAngularUnitsSx(self):
		if self.geo_unit_derived!=ANGULAR_UNIT_SX:
			self.geo_unit_derived=ANGULAR_UNIT_SX
			self.translateDerivedGeoUnits()
	@pyqtSignature('') #prevents actions being handled twice
	def on_rdobt_dk_clicked(self):
		self.setRegionDK()
	@pyqtSignature('') #prevents actions being handled twice
	def on_rdobt_faroe_clicked(self):
		self.setRegionFO()
	@pyqtSignature('') #prevents actions being handled twice
	def on_rdobt_greenland_clicked(self):
		self.setRegionGR()
	@pyqtSignature('') #prevents actions being handled twice
	def on_rdobt_world_clicked(self):
		self.setRegionWorld()
	#SETTINGS for Geo units - should be global??
	@pyqtSignature('') #prevents actions being handled twice
	def on_rdobt_settings_dg_clicked(self):
		old_unit=self.geo_unit
		self.geo_unit="dg"
		if old_unit!=self.geo_unit:
			self.translateGeoUnits()
	@pyqtSignature('') #prevents actions being handled twice
	def on_rdobt_settings_nt_clicked(self):
		old_unit=self.geo_unit
		self.geo_unit="nt"
		if old_unit!=self.geo_unit:
			self.translateGeoUnits()
	@pyqtSignature('') #prevents actions being handled twice
	def on_rdobt_settings_sx_clicked(self):
		old_unit=self.geo_unit
		self.geo_unit="sx"
		if old_unit!=self.geo_unit:
			self.translateGeoUnits()
	@pyqtSignature('') #prevents actions being handled twice
	def on_rdobt_settings_radians_clicked(self):
		old_unit=self.geo_unit
		self.geo_unit="radians"
		if old_unit!=self.geo_unit:
			self.translateGeoUnits()
			
	def translateGeoUnits(self):
		if self.output_cache.is_valid and TrLib.IsGeographic(self.output_cache.mlb) :
			self.setOutput(self.output_cache.coords,self.output[:2],self.output_cache.mlb)
		if TrLib.IsGeographic(str(self.cb_input_system.currentText())):
			for field in self.input[:2]:
				self.translateAngularField(field,self.geo_unit)
		if TrLib.IsGeographic(str(self.cb_bshlm_system.currentText())):
			for field in self.input_bshlm:
				self.translateAngularField(dield,self.geo_unit)
		for field in self.output_bshlm_geo:
			self.translateAngularField(field,self.geo_unit)
		for key in self.action_angular_units.keys():
			self.action_angular_units[key].setChecked(self.geo_unit==key)
		
	def translateDerivedGeoUnits(self):
		for field in self.derived_angular_output:
			self.translateAngularField(field,self.geo_unit_derived)
		for key in self.action_angular_units_derived.keys():
			self.action_angular_units_derived[key].setChecked(self.geo_unit_derived==key)	
	
	def translateAngularField(self,field,geo_unit):
		try:
			ang=TranslateToDegrees(str(field.text()),geo_unit)
		except Exception,msg:
			if DEBUG:
				self.log_interactive(repr(msg))
			return
		
		field.setText("%s" %TranslateFromDegrees(ang,geo_unit))
	
	def onShowScale(self):
		if (self.chb_show_scale.isChecked() and self.output_cache.is_valid):
			self.txt_scale.setText("%.8f" %self.output_cache.scale)
			self.txt_meridian_convergence.setText(TranslateFromDegrees(self.output_cache.meridian_convergence,self.geo_unit_derived))
			if DEBUG:
				self.log_interactive(repr(self.output_cache.coords)+"\n"+self.output_cache.mlb)
		else:
			self.txt_scale.setText("")
			self.txt_meridian_convergence.setText("")
	


	#a generel output field setter#
	def setOutput(self,coords,fields,mlb,z_fields=[2]):
		if len(coords)==0:
			for field in fields:
				field.clear()
			return
		is_geo=TrLib.IsGeographic(mlb)
		for i in range(len(fields)):
			if is_geo and (not i in z_fields):
				fields[i].setText("%s" %(TranslateFromDegrees(coords[i],self.geo_unit)))
			else:
				#TODO: global precision here
				fields[i].setText("%.4f m" %coords[i])
				
	#a general input converter#		
	def getInput(self,fields,mlb_in,z_fields=[2]):
		coords=[]
		is_geo=TrLib.IsGeographic(mlb_in)
		for i in range(len(fields)):
			field=fields[i]
			inp=str(field.text()).replace(" ","")
			try:
				if is_geo and (not i in z_fields):
					inp=TranslateToDegrees(inp,self.geo_unit)
				else:
					inp=inp.replace("m","")
				inp=float(inp)
			except Exception,msg:
				if DEBUG:
					self.log_interactive(repr(msg))
				return coords
			else:
				coords.append(inp)
		return coords
	
	def getInteractiveInput(self,mlb_in=None):
		if mlb_in is None:
			mlb_in=str(self.cb_input_system.currentText())
		coords=self.getInput(self.input,mlb_in)
		return coords
	
	def setInteractiveOutput(self,coords,mlb_out=None):
		#if coords==[] we clear output fields#
		if mlb_out is None:
			mlb_out=str(self.cb_output_system.currentText())
		mlb_out=str(self.cb_output_system.currentText())
		self.setOutput(coords,self.output,mlb_out,z_fields=[2])
		
		
		
	def setInteractiveInput(self,coords,mlb_in=None):
		if mlb_in is None:
			mlb_in=str(self.cb_input_system.currentText())
		self.setOutput(coords,self.input,mlb_in,z_fields=[2])
		
		
	def transform_input(self):
		self.log_interactive("",clear=True)
		self.output_cache.is_valid=False
		mlb_in=str(self.cb_input_system.currentText())
		mlb_out=str(self.cb_output_system.currentText())
		coords=self.getInteractiveInput(mlb_in)
		if len(coords)!=3:
			self.log_interactive("Input coordinate in field %d not OK!" %(len(coords)+1))
			self.setInteractiveOutput([])
			self.onShowScale()
			self.input[len(coords)].setFocus()
			return
		x_in,y_in,z_in=coords
		if self.CoordinateTransformation is None or mlb_in!=self.CoordinateTransformation.mlb_in or mlb_out!=self.CoordinateTransformation.mlb_out:
			try:
				ct=TrLib.CoordinateTransformation(mlb_in,mlb_out)
			except:
				self.log_interactive("Input labels not OK!")
				return None,None,None
			else:
				if self.CoordinateTransformation is not None:
					self.CoordinateTransformation.Close()
				self.CoordinateTransformation=ct
		x,y,z=self.transform(self.CoordinateTransformation,x_in,y_in,z_in)
		if x is None:
			self.setInteractiveOutput([])
			self.onShowScale()
			return
		#Cache output after succesfull transformation#
		self.output_cache.is_valid=True
		self.output_cache.mlb=mlb_out
		self.output_cache.coords=[x,y,z]
		#Always cache scale and convergence on succes....
		sc,m=self.CoordinateTransformation.GetLocalGeometry(x,y)
		self.output_cache.scale=sc
		self.output_cache.meridian_convergence=m
		self.setInteractiveOutput([x,y,z]) #here we cache scale ond convergence also!
		self.onShowScale()
		h_mlb1=Minilabel.ChangeHeightSystem(mlb_out,["N"])
		h_mlb2=Minilabel.ChangeHeightSystem(mlb_out,["E"])
		if self.HeightTransformation is None or h_mlb1!=self.HeightTransformation.mlb_in or h_mlb2!=self.HeightTransformation.mlb_out:
			try:
				ct=TrLib.CoordinateTransformation(h_mlb1,h_mlb2)
			except:
				self.log_interactive("Input labels not OK!")
				return None,None,None
			else:
				if self.HeightTransformation is not None:
					self.HeightTransformation.Close()
				self.HeightTransformation=ct
		x,y,z=self.transform(self.HeightTransformation,x,y,0)
		#self.log("%s %.2f" %(h_mlb,z))
		if x is not None:
			self.txt_geoid_height.setText("%.4f m" %z)
		geoid_name=self.CoordinateTransformation.GetGeoidName()
		if DEBUG:
			self.log_interactive("Geoid: %s" %geoid_name)
		self.txt_geoid_name.setText(geoid_name)
		self.drawPoint(x_in,y_in,mlb_in)
	
		
	def transform(self,transformation,x,y,z):
		try:	
			x,y,z=transformation.Transform(x,y,z)
		except:
			self.log_interactive("%.2f %.2f %.2f" %(x,y,z))
			err=TrLib.GetLastError()
			self.log_interactive("Error in transformation: %d" %err)
			if err in ERRORS:
				self.log_interactive("%s" %ERRORS[err])
			return None,None,None
		return x,y,z
	#TAB  File2File#
	def initF2FTab(self):
		#Auto completion - dont do it for now as input might not be a *file*
		#completer=QCompleter()
		#completer.setModel(QDirModel(completer))
		#completer.setCompletionMode(QCompleter.InlineCompletion)
		#self.txt_f2f_input_file.setCompleter(completer)
		if not self.has_ogr:
			self.rdobt_f2f_ogr.setEnabled(False)
			self.log_f2f("OGR library not available. A proper gdal installation might not be present?")
			self.tab_ogr.setEnabled(False)
			return
		if IS_LOCAL_GDAL:
			self.log_f2f("Using local GDAL installation.")
		frmts=File2File.GetOGRFormats()
		self.cb_f2f_ogr_driver.addItems(frmts)
		File2File.SetCommand(TROGR)
		rc,msg=File2File.TestCommand()
		if (rc!=0):
			self.message("Batch transformation program %s not availabe!" %TROGR)
			self.tab_ogr.setEnabled(False)
		self.log_f2f(msg)
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
		if len(self.f2f_settings.output_files)>1:
			self.log_f2f("Many output files - will try to view the first one...")
		fname=self.f2f_settings.output_files[0]
		dlg=TextViewer(self,fname=fname)
		dlg.show()
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
		dlg.show()
	#Event handlers for various buttons in f2f-tab#
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_change_h_in_clicked(self):
		mlb_in=str(self.cb_f2f_input_system.currentText())
		mlb=Minilabel.ChangeHeightSystem(mlb_in,H_SYSTEMS[self.region])
		if mlb!=mlb_in:
			self.cb_f2f_input_system.setEditText(mlb)
			self.onF2FSystemInChanged()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_change_h_out_clicked(self):
		mlb_out=str(self.cb_f2f_output_system.currentText())
		mlb=Minilabel.ChangeHeightSystem(mlb_out,H_SYSTEMS[self.region])
		if mlb!=mlb_out:
			self.cb_f2f_output_system.setEditText(mlb)
			self.onF2FSystemOutChanged()
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_browse_input_clicked(self):
		my_file = QFileDialog.getOpenFileName(self, "Select a vector-data input file",self.dir)
		if len(my_file)>0:
			self.txt_f2f_input_file.setText(my_file)
			self.dir=os.path.dirname(str(my_file))
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_browse_input_dir_clicked(self):
		my_file = QFileDialog.getExistingDirectory(self, "Select an input directory",self.dir)
		if len(my_file)>0:
			self.txt_f2f_input_file.setText(my_file)
			self.dir=os.path.dirname(str(my_file))
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_browse_output_clicked(self):
		my_file = QFileDialog.getSaveFileName(self, "Select a vector-data output file",self.dir)
		if len(my_file)>0:
			self.txt_f2f_output_file.setText(my_file)
			self.dir=os.path.dirname(str(my_file))
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_browse_output_dir_clicked(self):
		my_file = QFileDialog.getExistingDirectory(self, "Select an output directory",self.dir)
		if len(my_file)>0:
			self.txt_f2f_output_file.setText(my_file)
			self.dir=os.path.dirname(str(my_file))
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_browse_log_clicked(self):
		my_file = QFileDialog.getSaveFileName(self, "Select a log file",self.dir)
		if len(my_file)>0:
			self.txt_f2f_log_name.setText(my_file)
			self.dir=os.path.dirname(str(my_file))
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_input_layers_clicked(self):
		inname=str(self.txt_f2f_input_file.text())
		if len(inname)>0:
			ds=File2File.Open(inname)
			if ds is not None:
				layers=File2File.GetLayerNames(ds)
				File2File.Close(ds)
				dlg=LayerSelector(self,layers,self.txt_f2f_layers_in)
				dlg.show()
			else:
				self.message("Failed to open %s" %inname)
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_f2f_list_formats_clicked(self):
		text=File2File.ListFormats()
		self.log_f2f(text,"blue")
	def onF2FSystemInChanged(self):
		mlb_in=str(self.cb_f2f_input_system.currentText())
		text=self.GetDescription(mlb_in)
		self.lbl_f2f_input_info.setText("Input system info: %s" %text)
	def onF2FSystemOutChanged(self):
		mlb_out=str(self.cb_f2f_output_system.currentText())
		text=self.GetDescription(mlb_out)
		self.lbl_f2f_output_info.setText("Output system info: %s" %text)		
	def transformFile2File(self):
		file_in=str(self.txt_f2f_input_file.text())
		file_out=str(self.txt_f2f_output_file.text())
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
		if len(mlb_out)==0:
			self.message("Output system label must be specified!")
			return
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
			log_name=str(self.txt_f2f_log_name.text())
			if len(log_name)==0:
				self.message("Specify log file name.")
				return
			self.f2f_settings.be_verbose=self.chb_f2f_verbose.isChecked()
		else:
			log_name=None
			self.f2f_settings.be_verbose=False
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
		ok,msg=File2File.TransformDatasource(self.f2f_settings,self.message_poster.PostFileMessage,self.message_poster.PostReturnCode)
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
		self.log_f2f("Sending kill signal...")
		File2File.KillThreads()
	def onF2FReturnCode(self,rc):
		if rc==TrLib.TR_OK:
			self.log_f2f("....done....")
		elif rc==File2File.PROCESS_TERMINATED:
			self.log_f2f("Process was terminated!")
		#we're running - a method terminating the process could also enable buttons... and probably will#
		self.f2f_settings.is_done=True
		self.bt_f2f_execute.setEnabled(True)
		self.bt_f2f_view_output.setEnabled(True)
		self.bt_f2f_view_log.setEnabled(True)
		self.bt_f2f_kill.setEnabled(False)
	#TAB BESSEL HELMERT#
	@pyqtSignature('') #prevents actions being handled twice
	def on_chb_bshlm_custom_ellipsoid_clicked(self):
		is_custom=self.chb_bshlm_custom_ellipsoid.isChecked()
		if is_custom:
			self.cb_bshlm_system.setEnabled(False)
			self.txt_bshlm_ellipsoid.setText("custom")
			self.txt_bshlm_axis.setEnabled(True)
			self.txt_bshlm_flattening.setEnabled(True)
			labels=SYSTEM_LABELS[Minilabel.GEO_CODE]
			self.lbl_bshlm_description.setText("Custom ellipsoid - geographical coordinates")
			for i in range(2):
				self.input_labels_bshlm[i].setText(labels[i])
		else:
			self.cb_bshlm_system.setEnabled(True)
			self.txt_bshlm_axis.setEnabled(False)
			self.txt_bshlm_flattening.setEnabled(False)
			self.onBshlmSystemChanged()
	def onBshlmSystemChanged(self):
		mlb=str(self.cb_bshlm_system.currentText())
		if len(mlb)==0:
			return
		text=self.GetDescription(mlb)
		self.lbl_bshlm_description.setText("%s" %text)
		sys_code=Minilabel.GetSysCode(mlb)
		if sys_code in SYSTEM_LABELS:
			labels=SYSTEM_LABELS[sys_code]
			for i in range(2):
				self.input_labels_bshlm[i].setText(labels[i])
		region,proj,dtm,h_datum,htype=TrLib.SplitMLB(mlb)
		if len(dtm)==0: #if implicit datum...
			descr,dtm=TrLib.DescribeProjection(proj)
		name,a,f=TrLib.GetEllipsoidParametersFromDatum(dtm)
		if name is not None:
			self.txt_bshlm_ellipsoid.setText(name)
			self.txt_bshlm_axis.setText("%.4f m" %a)
			if 0<f<1:
				sf=1/f
			else:
				sf=f
			self.txt_bshlm_flattening.setText("%.8f" %sf)
		else:
			self.message("Could not find ellipsoid! %s %s" %(geo_mlb,mlb))
	def doBesselHelmert(self):
		#TODO: Improve
		is_custom=self.chb_bshlm_custom_ellipsoid.isChecked()
		if not is_custom:
			mlb=str(self.cb_bshlm_system.currentText())
			if len(mlb)==0:
				#perhaps emit a warning?
				return
			geo_mlb=TrLib.Convert2Geo(mlb)
		else:
			mlb="geo"
			geo_mlb="geo"
		
		is_mode1=self.rdobt_bshlm_mode1.isChecked()
		#Get needed input
		if is_mode1:
			coords=self.getInput(self.input_bshlm,mlb,z_fields=[])
			if len(coords)!=4:
				self.log_bshlm("Input coordinate %d not OK" %(len(coords)+1))
				self.input_bshlm[len(coords)].setFocus()
				return
			x1,y1,x2,y2=coords
			
		else:
			coords=self.getInput(self.input_bshlm[0:2],mlb,z_fields=[])
			if len(coords)!=2:
				self.log_bshlm("Station1 coordinates not OK")
				self.input_bshlm[len(coords)].setFocus()
				return
			input_data=self.getInput(self.input_bshlm_azimuth,geo_mlb,z_fields=[0])
			if len(input_data)!=2:
				self.log_bshlm("Input distance and azimuth not OK")
				self.input_bshlm_azimuth[len(input_data)].setFocus()
				if (DEBUG):
					self.log_interactive(repr(input_data))
				return
			x1,y1=coords
			
			dist,a1=input_data
		ell_data=self.getInput([self.txt_bshlm_axis,self.txt_bshlm_flattening],"",z_fields=[0,1])
		if len(ell_data)==2:
			a,f=ell_data
		else:
			self.message("Error in ellipsoid data!")
			return
		#end get needed input#
		#transform to geo coords if needed#
		if not is_custom:
			try:
				ct=TrLib.CoordinateTransformation(mlb,geo_mlb)
			except:
				self.message("Input labels not OK!")
				return
			try:
				x1,y1,z=ct.Transform(x1,y1)
			except:
				self.message("Error in transformation of coords for station1")
				ct.Close()
				return
		#display output of first transformation, x1,y1 should now alwyas be in geo-coords#
		self.setOutput([x1,y1],self.output_bshlm_geo[:2],geo_mlb,z_fields=[])
		
		#Now get the other output from bshlm and transformations....
		if is_mode1:
			if not is_custom:
				try: #transform to geographic
					x2,y2,z=ct.Transform(x2,y2)
				except:
					self.message("Error in transformation of coords for station2")
					ct.Close()
					return
			
			data=TrLib.BesselHelmert(a,f,x1,y1,x2,y2)
			if data[0] is not None:
				a1,a2=data[1:]
				self.setOutput(data,self.output_bshlm_azimuth,geo_mlb,z_fields=[0])
			else:
				self.message("Error: could not calculate azimuth!")
		else:
			data=TrLib.InverseBesselHelmert(a,f,x1,y1,a1,dist)
			if data[0] is not None:
				x2,y2,a2=data
				if not is_custom:
					try:
						x2_out,y2_out,z2=ct.InverseTransform(x2,y2)
					except:
						self.message("Error in transformation of coords for station2")
				else:
					x2_out=x2
					y2_out=y2
				#display result...
				self.setOutput([x2_out,y2_out],self.input_bshlm[2:],mlb,z_fields=[])
				
				self.txt_bshlm_azimuth2.setText(TranslateFromDegrees(a2,self.geo_unit))
			else:
				self.message("Error: could not do inverse Bessel Helmert calculation")
		#always display ouput in geo field - even if not transformed
		self.setOutput([x2,y2],self.output_bshlm_geo[2:],geo_mlb,z_fields=[])
		self.log_bshlm("Successful calculation....",clear=True)
		if not is_custom:
			ct.Close()
	
	#TAB PYTHON#
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_python_load_clicked(self):
		if self.script_dir is None:
			dir=self.dir
		else:
			dir=self.script_dir
		my_file = str(QFileDialog.getOpenFileName(self, "Select a python script file",dir,"*.py"))
		if len(my_file)>0:
			self.script_dir=os.path.dirname(my_file)
			try:
				f=open(my_file)
			except:
				self.message("Unable to open file!")
			else:
				txt=f.read()
				self.txt_python_in.setText(txt)
				f.close()
				self.chb_python_process_enter.setChecked(False)
	def onPythonCommand(self):
		if HAS_QSCI:
			cmd=str(self.txt_python_in.text()).strip()
		else:
			cmd=str(self.txt_python_in.toPlainText()).strip()
		if len(cmd)==0:
			return
		if cmd.lower()=="clear":
			self.txt_python_out.clear()
			
		elif cmd.lower()=="help":
			self.onHelp_local()
			
		elif cmd.lower().replace(" ","")=="help()":
			self.log_pythonStdOut("Interactive python help is not available in this mode...")
		elif cmd.lower()=="example":
			self.pythonExample()
			return
		else:	
			ok=self.python_console.ExecuteCode(cmd)
			if self.chb_python_clear.isChecked() and ok:
				self.clearPythonIn()
			return
		self.clearPythonIn()
	def clearPythonIn(self):
		self.txt_python_in.clear()
		if HAS_QSCI:
			self.txt_python_in.setCursorPosition(0,0)
	#really subclassing the TextEdit/Qscintilla object - however this is more convenient when using designer...	
	def onPythonKey(self,event):
		if (not event.isAutoRepeat()):
			if event.key()==Qt.Key_Up and self.chb_python_process_enter.isChecked() and len(self.python_console.cmd_buffer)>0:
				event.accept()
				text=self.python_console.SpoolUp()
				self.txt_python_in.setText(text)
				return
			if event.key()==Qt.Key_Down and self.chb_python_process_enter.isChecked() and len(self.python_console.cmd_buffer)>0:
				event.accept()
				text=self.python_console.SpoolDown()
				self.txt_python_in.setText(text)
				return
			if event.key()==Qt.Key_Return and self.chb_python_process_enter.isChecked():
				event.accept()
				self.onPythonCommand()
				return
		type(self.txt_python_in).keyPressEvent(self.txt_python_in,event)
		#if HAS_QSCI:
		#	Qsci.Qscintilla.keyPressEvent(self.txt_python_in,event)
		#else:
		#	QTextEdit.keyPressEvent(self.txt_python_in,event)
	def pythonExample(self):
		stars="*"*50
		self.log_pythonStdOut(stars,"blue")
		self.log_pythonStdOut("Running example code:","blue")
		code=["GetVersion()","Transform('geoEed50','utm32Hwgs84_h_dvr90',11.75,54.10,100)",
		"wkt=GetEsriText('utm32_etrs89')","print wkt",
		"ImportLabel(wkt)","ImportLabel('EPSG:25832')"]
		for cmd in code:
			self.log_pythonStdOut(cmd,"blue")
			self.python_console.ExecuteCode(cmd)
		self.log_pythonStdOut(stars,"blue")
	#MESSAGE AND LOG METHODS#
	def log_interactive(self,text,color="black",clear=False):
		self.txt_log.setTextColor(QColor(color))
		if clear:
			self.txt_log.setText(text)
		else:
			self.txt_log.append(text)
		self.txt_log.ensureCursorVisible()
	def log_f2f(self,text,color="black",insert=False):
		self.txt_f2f_log.setTextColor(QColor(color))
		if insert:
			self.txt_f2f_log.insertPlainText(text)
		else:
			self.txt_f2f_log.append(text)
		self.txt_f2f_log.repaint()
		self.txt_f2f_log.ensureCursorVisible()
	def log_bshlm(self,text,color="black",clear=False):
		self.txt_bshlm_log.setTextColor(QColor(color))
		if (not clear):
			self.txt_bshlm_log.append(text)
		else:
			self.txt_bshlm_log.setText(text)
		self.txt_bshlm_log.ensureCursorVisible()
	def log_python(self,text,color="green"):
		self.txt_python_out.setTextColor(QColor(color))
		self.txt_python_out.append(text)
		self.txt_python_out.ensureCursorVisible()
	def message(self,text,title="Error"):
		QMessageBox.warning(self,title,text)
	def log_pythonStdOut(self,text,color="green"):
		self.log_python(text,color)
	def log_pythonStdErr(self,text,color="red"):
		self.log_python(text,color)
	def displayCallbackMessage(self,text):
		i=self.tab_gsttrans.currentIndex()
		if i in self.log_method_map:
			self.log_method_map[i](text,"blue")
		else:
			self.message(text)
	#SETTINGS#
	def saveSettings(self):
		settings = QSettings(COMPANY_NAME,PROG_NAME)
		settings.beginGroup('MainWindow')
		settings.setValue('size', self.size())
		settings.setValue('position', self.pos())
		settings.endGroup()
		settings.beginGroup('data')
		settings.setValue('geoids',self.geoids)
		settings.setValue('path',self.dir)
		settings.setValue('script_path',self.script_dir)
		settings.endGroup()
	def loadSettings(self):
		settings = QSettings(COMPANY_NAME,PROG_NAME)
		settings.beginGroup('MainWindow')
		self.resize(settings.value('size', self.size()).toSize())
		self.move(settings.value('position', self.pos()).toPoint())
		settings.endGroup()
		settings.beginGroup('data')
		geoids=settings.value('geoids')
		if geoids.isValid():
			self.geoids=str(geoids.toString())
		else:
			self.geoids=None
		dir=settings.value('path')
		if dir.isValid():
			self.dir=str(dir.toString())
		else:
			self.dir=DEFAULT_DIR
		dir=settings.value('script_path')
		if dir.isValid():
			self.script_dir=str(dir.toString())
		else:
			self.script_dir=self.dir
		settings.endGroup()
		
	def selectTabDir(self):
		my_file = str(QFileDialog.getExistingDirectory(self, "Select a geoid directory",self.dir))
		return my_file
	def changeTabDir(self):
		my_file = self.selectTabDir()
		if len(my_file)>0:
			ok,msg=TrLib.SetGeoidDir(my_file)
			if ok:
				self.lbl_geoid_dir_value.setText(os.path.realpath(my_file))
				self.geoids=my_file
				os.environ["TR_TABDIR"]=self.geoids
			else:
				self.message("Failed to set geoid dir!\n%s" %msg)
	#PLUGIN LOADER#
	def loadPlugins(self):
		plugins=GetPlugins(PLUGIN_PATH)
		if len(plugins)>0:
			if not HAS_IMPORTLIB:
				self.log_pythonStdOut("Plugin loader needs importlib (python version>=2.7)",color="red")
				return
			if not PLUGIN_PATH in sys.path:
				sys.path.insert(0,PLUGIN_PATH)
			for plugin in plugins:
				self.log_python("Loading plugin: %s" %plugin,color="brown")
				try:
					_plugin=importlib.import_module(plugin)
				except Exception,msg:
					print repr(msg)
				else:
					#Test if this is a widget type plugin!
					if hasattr(_plugin,"getWidget"):
						self.addPluginWidget(_plugin)
					self.python_console.python_locals[plugin]=_plugin
		else:
			self.log_pythonStdOut("No python plugins in "+PLUGIN_PATH)
	#Add TAB - for widget type plugins#
	def addPluginWidget(self,plugin):
		#TODO: implement a manager, which allows enabling/disabling plugins - which means that we should store info 
		#on loaded plugins and tab positions....
		if hasattr(plugin,"getName"):
			name=plugin.getName()
		else:
			name="some_plugin"
		self.log_python("Widget type plugin - added as tab: %s" %name,color="brown")
		widget=plugin.getWidget(self)
		self.tab_gsttrans.addTab(widget,name)
	#ON CLOSE - SAVE SETTINGS#
	def closeEvent(self, event):
		self.saveSettings()
		QMainWindow.closeEvent(self, event)
		

if __name__=="__main__":
	 global app
	 global MainWindow
	 app = QtGui.QApplication(sys.argv)
	 MainWindow = GSTtrans()
	 MainWindow.show()
	 sys.exit(app.exec_())
	
	
		
