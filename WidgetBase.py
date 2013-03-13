##########################################################################
## A template class for widget based plugins or simply extra tabs which are implemented as separate modules.
## simlk, March 2013.
##########################################################################
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


from PyQt4 import QtCore, QtGui

class WidgetBase(QtGui.QWidget):
	#Parent is a handle to the main window of the application - a QMainWindow instance. 
	#Store this handle if you want to interact with the main window - it is also possible to modify the main window through this handle.
	def __init__(self,parent):
		QtGui.QWidget.__init__(self,parent)
	#Implement this methos to handle textual call back messages from the transformation library
	def handleCallBack(self,text):
		pass
	#Implement this method to handle text output from python stdout
	def handleStdOut(self,text):
		pass
	#Implement this method to handle text output from python stderr
	def handleStdErr(self,text):
		pass
	#Implement this method to handle a global change in region - e.g. if you want to display different data depending on region.
	#region input will be one of the regions defined in TrLib_constants
	def handleRegionChange(self,region):
		pass
	#Implement this method to handle a global change in angular units for GEOGRAPHICAL COORDINATE SYSTEMS.
	#unit input will be one of the angular units defined in TrLib_constants
	def handleGeoUnitChange(self,unit):
		pass
	#Implement this method to handle a global change in angular units for derived output like e.g. azimuths.
	#unit input will be one of the angular units defined in TrLib_constants
	def handleAngularUnitChange(self,unit):
		pass
		
	