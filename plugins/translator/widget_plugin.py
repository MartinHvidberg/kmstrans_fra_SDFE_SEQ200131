from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from translator_ui import Ui_TranslatorWidget
import TrLib
class TranslatorWidget(QWidget):
	def __init__(self,parent):
		QWidget.__init__(self,parent)
		self.ui=Ui_TranslatorWidget()
		self.ui.setupUi(self)
		self.ui.txt_epsg.returnPressed.connect(self.onEPSG)
		self.ui.txt_proj4.returnPressed.connect(self.onProj4)
		self.ui.txt_wkt.keyPressEvent=self.onWktKey
		self.ui.txt_mlb.returnPressed.connect(self.onMLB)
		
	def translateForeign(self,txt):
		if len(txt)>0:
			mlb=TrLib.ImportLabel(txt)
			if mlb is not None and len(mlb)>0:
				self.ui.txt_mlb.setText(mlb)
				descr=TrLib.DescribeLabel(mlb)
				self.ui.lbl_system_info.setText("System: "+descr)
				return
		self.ui.lbl_system_info.setText("System: No translation")
		self.ui.txt_mlb.setText("No translation")
		
	def onEPSG(self):
		txt=str(self.ui.txt_epsg.text())
		if not txt.startswith("EPSG:"):
			txt="EPSG:"+txt
		self.translateForeign(txt)
	def onProj4(self):
		txt=str(self.ui.txt_proj4.text())
		self.translateForeign(txt)
	def onWktKey(self,event):
		if (not event.isAutoRepeat()):
			if event.key()==Qt.Key_Return:
				event.accept()
				self.translateForeign(str(self.ui.txt_wkt.toPlainText()))
				return
		type(self.ui.txt_wkt).keyPressEvent(self.ui.txt_wkt,event)
	def onMLB(self):
		mlb=str(self.ui.txt_mlb.text())
		if len(mlb)>0:
			descr=TrLib.DescribeLabel(mlb)
			wkt=TrLib.ExportLabel(mlb,"WKT")
			epsg=TrLib.ExportLabel(mlb,"EPSG")
			proj4=TrLib.ExportLabel(mlb,"PROJ4")
			
			if wkt is not None and len(wkt)>0:
				self.ui.txt_wkt.setText(wkt)
			else:
				self.ui.txt_wkt.setText("No translation")
			if epsg is not None and len(epsg)>0:
				self.ui.txt_epsg.setText(epsg)
			else:
				self.ui.txt_epsg.setText("No translation")
			if proj4 is not None and len(proj4)>0:
				self.ui.txt_proj4.setText(proj4)
			else:
				self.ui.txt_proj4.setText("No translation")
			self.ui.lbl_system_info.setText("System: "+descr)
	def handleCallBack(self,text):
		self.ui.txt_log.append(text)
	def handleStdOut(self,text):
		self.ui.txt_log.append(text)
	def handleStdErr(self,text):
		self.ui.txt_log.append(text)