####################################
## A plugin like implementation of the python console tab for trui
## simlk, March 2013
####################################
# Copyright (c) 2013, National Geodata Agency, Denmark
# (Geodatastyrelsen), gst@gst.dk
# 
# Permission to use, copy, modify, and/or distribute this software for any
#purpose with or without fee is hereby granted, provided that the above
#copyright notice and this permission notice appear in all copies.
#  
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN 
#ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
import sys
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
try:
	from PyQt4 import Qsci
except:
	HAS_QSCI=False
else:
	HAS_QSCI=True
from WidgetBase import WidgetBase
from Tab_python import  Ui_tab_python
import EmbedPython
import TrLib
class PythonWidget(WidgetBase,Ui_tab_python):
	def __init__(self,parent):
		WidgetBase.__init__(self,parent)
		self.parent=parent
		self.setupUi(self)
		#Event handlers#
		self.bt_python_run.clicked.connect(self.onPythonCommand)
		#Setup namespaces etc, log stufff.
		self.log_python("Python version:\n"+sys.version,color="green")
		self.log_python("TrLib version:\n"+TrLib.GetVersion(),color="green")
		namespace={"loadPlugins":parent.loadPlugins,"mainWindow":parent}
		self.log_python("Handle to main window %s stored in name: mainWindow" %repr(parent.__class__),color="brown")
		self.python_console=EmbedPython.PythonConsole(namespace)
		self.python_console.ExecuteCode("from TrLib import *")
		self.log_python("from TrLib import *  - Loading namespace from TrLib.py",color="brown")
		self.log_python("Type 'example' to run example code",color="blue")
		self.log_python("Type 'clear' to clear output field",color="blue")
		#Determine what type the input text field should be and setup its event handler....
		if HAS_QSCI:
			self.txt_python_in=Qsci.QsciScintilla(self)
			self.txt_python_in.setLexer(Qsci.QsciLexerPython())
			self.txt_python_in.setAutoIndent(True)
		else:
			self.txt_python_in=QTextEdit(self)
		self.layout().addWidget(self.txt_python_in)
		self.txt_python_in.keyPressEvent=self.onPythonKey
		if not HAS_QSCI:
			self.log_python("Qscintilla not installed. Python input lexer will not work...",color="red")
		self.python_console.ClearCache()
		self.txt_python_in.setWhatsThis("Enter/edit input python code here")
	def addModule(self,module,name):
		self.python_console.python_locals[name]=module
		self.log_python("Adding plugin: %s" %name,color="brown")
	#TAB PYTHON#
	@pyqtSignature('') #prevents actions being handled twice
	def on_bt_python_load_clicked(self):
		#Hmmm - some logic to consider here - path attributtes shared between this widget and the main window?
		if self.parent.script_dir is None:
			dir=self.parent.dir
		else:
			dir=self.parent.script_dir
		my_file = str(QFileDialog.getOpenFileName(self, "Select a python script file",dir,"*.py"))
		if len(my_file)>0:
			self.parent.script_dir=os.path.dirname(my_file)
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
			self.log_python("Interactive python help is not available in this mode...",color="red")
		elif cmd.lower()=="example":
			self.pythonExample()
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
		
	def pythonExample(self):
		stars="*"*50
		self.log_python(stars,"blue")
		self.log_python("Running example code:","blue")
		code=["GetVersion()","Transform('geoEed50','utm32Hwgs84_h_dvr90',11.75,54.10,100)",
		"wkt=GetEsriText('utm32_etrs89')","print wkt",
		"ImportLabel(wkt)","ImportLabel('EPSG:25832')"]
		for cmd in code:
			self.log_python(cmd,"blue")
			self.python_console.ExecuteCode(cmd)
		self.log_python(stars,"blue")
	def log_python(self,text,color="green"):
		self.txt_python_out.setTextColor(QColor(color))
		self.txt_python_out.append(text)
		self.txt_python_out.ensureCursorVisible()
	#Override methods for textual output#
	def handleCallBack(self,text):
		self.log_python(text,"blue")
	def handleStdOut(self,text):
		self.log_python(text,"green")
	def handleStdErr(self,text):
		self.log_python(text,"red")
		