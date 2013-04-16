###################
## A "plugin like" implementation of the Bessel Helmert tab for trui
## simlk, March 2013
###################
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
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from WidgetBase import WidgetBase
from Tab_bshlm import  Ui_tab_bshlm
import TrLib
import Minilabel
from TrLib_constants import *
import WidgetUtils
#Default systems pr. region:
BSHLM_SYS_DK=["utm32_etrs89","utm33_etrs89","geo_etrs89","fcs","dktm1","dktm2","dktm3"]
BSHLM_SYS_FO=["fotm","fk89","utm28_wgs84","geo_wgs84"]
BSHLM_SYS_GR=["geo_gr96","utm24_gr96","utm25_gr96","utm26_gr96"]
BSHLM_SYS_WORLD=["geo_wgs84","mrc0_wgs84","webmrc"]
BSHLM_SYS_DEFAULT=["utm32_wgs84","geo_wgs84","mrc0_wgs84"]
BSHLM_SYSTEMS={"default":BSHLM_SYS_DEFAULT,
REGION_DK:BSHLM_SYS_DK,
REGION_FO:BSHLM_SYS_FO,
REGION_GR:BSHLM_SYS_GR,
REGION_WORLD:BSHLM_SYS_WORLD
}
class BshlmWidget(WidgetBase,Ui_tab_bshlm):
	def __init__(self,parent):
		WidgetBase.__init__(self,parent)
		self.setupUi(self)
		#convenient pointers#
		self.input_bshlm=[self.txt_bshlm_x1,self.txt_bshlm_y1,self.txt_bshlm_x2,self.txt_bshlm_y2]
		self.output_bshlm_geo=[self.txt_bshlm_lon1,self.txt_bshlm_lat1,self.txt_bshlm_lon2,self.txt_bshlm_lat2]
		self.output_bshlm_azimuth=[self.txt_bshlm_distance,self.txt_bshlm_azimuth1,self.txt_bshlm_azimuth2]
		self.input_bshlm_azimuth=self.output_bshlm_azimuth[:2]
		self.input_labels_bshlm=[self.lbl_bshlm_x,self.lbl_bshlm_y]
		self.derived_angular_output=self.output_bshlm_azimuth[1:]
		#SETUP BSHLM EVENT HANDLERS#
		for field in self.input_bshlm+self.input_bshlm_azimuth:
			field.returnPressed.connect(self.doBesselHelmert)
		self.cb_bshlm_system.currentIndexChanged.connect(self.onBshlmSystemChanged)
		self.geo_unit=parent.geo_unit
		self.geo_unit_derived=parent.geo_unit_derived
	#TAB BESSEL HELMERT#
	@pyqtSignature('') #prevents actions being handled twice
	def on_chb_bshlm_custom_ellipsoid_clicked(self):
		is_custom=self.chb_bshlm_custom_ellipsoid.isChecked()
		if is_custom:
			self.cb_bshlm_system.setEnabled(False)
			self.txt_bshlm_ellipsoid.setText("custom")
			self.txt_bshlm_axis.setEnabled(True)
			self.txt_bshlm_flattening.setEnabled(True)
			labels=SYSTEM_LABELS[GEO_CODE]
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
		text=TrLib.DescribeLabel(mlb)
		self.lbl_bshlm_description.setText("%s" %text)
		labels=Minilabel.GetSystemLabels(mlb)
		if labels is not None:
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
			mlb="geo_none"
			geo_mlb="geo_none"
		
		is_mode1=self.rdobt_bshlm_mode1.isChecked()
		#Get needed input
		is_geo_in=TrLib.IsGeographic(mlb)
		if is_mode1:
			coords,msg=WidgetUtils.getInput(self.input_bshlm,is_geo_in,z_fields=[],angular_unit=self.geo_unit)
			if len(coords)!=4:
				self.log_bshlm("Input coordinate %d not OK.\n%s" %(len(coords)+1,msg))
				self.input_bshlm[len(coords)].setFocus()
				return
			x1,y1,x2,y2=coords
			
		else:
			coords,msg=WidgetUtils.getInput(self.input_bshlm[0:2],is_geo_in,z_fields=[],angular_unit=self.geo_unit)
			if len(coords)!=2:
				self.log_bshlm("Station1 coordinates not OK.\n%s" %msg)
				self.input_bshlm[len(coords)].setFocus()
				return
			input_data,msg=WidgetUtils.getInput(self.input_bshlm_azimuth,True,z_fields=[0],angular_unit=self.geo_unit_derived)
			if len(input_data)!=2:
				self.log_bshlm("Input distance and azimuth not OK.\n%s" %msg)
				self.input_bshlm_azimuth[len(input_data)].setFocus()
				return
			x1,y1=coords
			
			dist,a1=input_data
		ell_data,msg=WidgetUtils.getInput([self.txt_bshlm_axis,self.txt_bshlm_flattening],False,z_fields=[0,1])
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
		WidgetUtils.setOutput([x1,y1],self.output_bshlm_geo[:2],True,z_fields=[],angular_unit=self.geo_unit)
		
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
				WidgetUtils.setOutput(data,self.output_bshlm_azimuth,True,z_fields=[0],angular_unit=self.geo_unit_derived)
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
				WidgetUtils.setOutput([x2_out,y2_out],self.input_bshlm[2:],is_geo_in,z_fields=[],angular_unit=self.geo_unit)
				
				self.txt_bshlm_azimuth2.setText(TranslateFromDegrees(a2,self.geo_unit_derived))
			else:
				self.message("Error: could not do inverse Bessel Helmert calculation")
		#always display ouput in geo field - even if not transformed
		WidgetUtils.setOutput([x2,y2],self.output_bshlm_geo[2:],True,z_fields=[],angular_unit=self.geo_unit)
		self.log_bshlm("Successful calculation....",clear=True)
		if not is_custom:
			ct.Close()
	def log_bshlm(self,text,color="black",clear=False):
		self.txt_bshlm_log.setTextColor(QColor(color))
		if (not clear):
			self.txt_bshlm_log.append(text)
		else:
			self.txt_bshlm_log.setText(text)
		self.txt_bshlm_log.ensureCursorVisible()
	#Override methods#
	def handleStdOut(self,text):
		self.log_bshlm(text,color="green")
	def handleStdErr(self,text):
		self.log_bshlm(text,color="red")
	def handleCallBack(self,text):
		self.log_bshlm(text,color="blue")
	def handleRegionChange(self,region):
		self.cb_bshlm_system.clear()
		if region in BSHLM_SYSTEMS:
			systems=BSHLM_SYSTEMS[region]
		else:
			systems=BSHLM_SYSTEMS["default"]
		self.cb_bshlm_system.addItems(systems)
	def handleGeoUnitChange(self,geo_unit):
		self.geo_unit=geo_unit
		if TrLib.IsGeographic(str(self.cb_bshlm_system.currentText())):
			for field in self.input_bshlm:
				WidgetUtils.translateAngularField(field,geo_unit)
		for field in self.output_bshlm_geo:
			WidgetUtils.translateAngularField(field,geo_unit)
	def handleAngularUnitChange(self,geo_unit):
		self.geo_unit_derived=geo_unit
		for field in self.derived_angular_output:
			WidgetUtils.translateAngularField(field,geo_unit)
	def message(self,text,title="Error"):
		QMessageBox.warning(self,title,text)