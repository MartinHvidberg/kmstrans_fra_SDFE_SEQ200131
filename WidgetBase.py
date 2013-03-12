from PyQt4 import QtCore, QtGui

class WidgetBase(QtGui.QWidget):
	def __init__(self,parent):
		QtGui.QWidget.__init__(self,parent)
	def handleCallBack(self,text):
		pass
	def handleStdOut(self,text):
		pass
	def handleStdErr(self,text):
		pass
	def handleRegionChange(self,region):
		pass
	def handleGeoUnitChange(self,unit):
		pass
	def handleAngularUnitChange(self,unit):
		pass
		
	