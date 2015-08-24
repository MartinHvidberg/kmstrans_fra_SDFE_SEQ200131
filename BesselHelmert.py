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
BSHLM_SYS_DK=["utm32_etrs89","utm33_etrs89","geo_etrs89","geo_ed50","fcs","dktm1","dktm2","dktm3","dktm4","kp2000j",
"kp2000s","kp2000b","s34j","s34s","s34b"]
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
class BshlmCache(object):
    def __init__(self):
        self.is_valid=False #flag which determines whether output fields are valid
        self.mlb=None
        self.geo_mlb=None
        self.ellipsoid=None
        self.is_custom=False #flag to turn on when using custom ellipsoid
        self.valid_label=False #flag to determine if the label is invalid
        self.axis=-1    #use negative numbers to signal something not valid...
        self.flattening=-1
        self.a1=0
        self.a2=0
        self.d=0
        self.proj_weakly_defined=False  #flag to use for s34 like systems (8 and 10)
        self.mode=0 #flag which tells whether the output was gotten by mode 1 ==0 or mode 2==1
        
class BshlmWidget(WidgetBase,Ui_tab_bshlm):
    def __init__(self,parent):
        WidgetBase.__init__(self,parent)
        self.setupUi(self)
        #convenient pointers#
        self.input_bshlm=[self.txt_bshlm_x1,self.txt_bshlm_y1,self.txt_bshlm_x2,self.txt_bshlm_y2]
        self.output_bshlm_geo=[self.txt_bshlm_lon1,self.txt_bshlm_lat1,self.txt_bshlm_lon2,self.txt_bshlm_lat2]
        self.output_bshlm_azimuth=[self.txt_bshlm_distance,self.txt_bshlm_azimuth1,self.txt_bshlm_azimuth2] #yep - bad naming, first field is the distance output/input
        self.input_bshlm_azimuth=self.output_bshlm_azimuth[:2]
        self.input_labels_bshlm=[self.lbl_bshlm_x,self.lbl_bshlm_y]
        self.derived_angular_output=self.output_bshlm_azimuth[1:]
        #SETUP BSHLM EVENT HANDLERS#
        self._handle_system_change=True  #flag to set when we want the event handler to just return - e.g. when removing a bad item...
        for field in self.input_bshlm+self.input_bshlm_azimuth:
            field.returnPressed.connect(self.doBesselHelmert)
        self.cb_bshlm_system.currentIndexChanged.connect(self.onBshlmSystemChanged)
        self.geo_unit=parent.geo_unit
        self.geo_unit_derived=parent.geo_unit_derived
        self.cache=BshlmCache()
        self.ed50_ellipsoid=TrLib.GetEllipsoidParametersFromDatum("ed50")
    #TAB BESSEL HELMERT#
    @pyqtSignature('') #prevents actions being handled twice
    def on_chb_bshlm_custom_ellipsoid_clicked(self):
        is_custom=self.chb_bshlm_custom_ellipsoid.isChecked()
        if is_custom:
            self.cb_bshlm_system.setEnabled(False)
            self.txt_bshlm_ellipsoid.setText("custom")
            self.txt_bshlm_axis.setEnabled(True)
            self.txt_bshlm_flattening.setEnabled(True)
            labels=Minilabel.getSystemLabels("geo_wgs84") # a dummy label
            self.lbl_bshlm_description.setText("Custom ellipsoid - geographical coordinates")
            for i in range(2):
                self.input_labels_bshlm[i].setText(labels[i])
            self.clearOutput()
        else:
            self.cb_bshlm_system.setEnabled(True)
            self.txt_bshlm_axis.setEnabled(False)
            self.txt_bshlm_flattening.setEnabled(False)
            self.onBshlmSystemChanged(False)
    #will be called on every transformation also in order to set correct info text and data also when return isn't pressed.
    def onBshlmSystemChanged(self,called_by_index_change=True):
        if not self._handle_system_change:
            return
        self.clearOutput()
        self.cache.is_valid=False #signal no valid output YET!
        self.cache.valid_label=False #will only be set to true if nothing goes wrong below....
        is_custom=self.chb_bshlm_custom_ellipsoid.isChecked()
        self.logBshlm("",clear=True)
        if (is_custom):
            self.cache.is_custom=True
            self.cache.mlb="custom"
            ell_data,msg=WidgetUtils.getInput([self.txt_bshlm_axis,self.txt_bshlm_flattening],False)
            if len(ell_data)!=2 or ell_data[0]<0 or ell_data[1]<0:
                self.logBshlm("Bad ellipsoid data:\n%s"%msg,"red")
                self.cache.valid_label=False
                return
            self.cache.axis=ell_data[0]
            self.cache.flattening=ell_data[1]
            self.cache.valid_label=True
        else:
            self.cache.is_custom=False
            mlb=str(self.cb_bshlm_system.currentText())
            if len(mlb)==0:
                return
            self.cache.mlb=mlb
            text=TrLib.DescribeLabel(mlb)
            self.lbl_bshlm_description.setText("%s" %text)
            labels=Minilabel.getSystemLabels(mlb)
            if labels is not None:
                for i in range(2):
                    self.input_labels_bshlm[i].setText(labels[i])
            if Minilabel.isProjWeaklyDefined(mlb):
                self.cache.proj_weakly_defined=True
                self.logBshlm("INFO: distance and azimuths will be calculated in ED50 datum","blue")
                name,a,f=self.ed50_ellipsoid
                self.cache.geo_mlb="geo_ed50"
            else:
                try:
                    dtm=TrLib.GetDatum(mlb)
                    name,a,f=TrLib.GetEllipsoidParametersFromDatum(dtm)
                    self.cache.geo_mlb=TrLib.Convert2Geo(mlb)
                except Exception,msg:
                    self.logBshlm("Invalid label:\n%s" %msg,"red")
                    if called_by_index_change: #if called by handler which adds label to list
                        self._handle_system_change=False
                        self.cb_bshlm_system.removeItem(self.cb_bshlm_system.currentIndex())
                        self.cb_bshlm_system.setEditText(mlb)
                        self._handle_system_change=True
                    return
            if name is not None:
                self.txt_bshlm_ellipsoid.setText(name)
                self.txt_bshlm_axis.setText("%.4f m" %a)
                if 0<f<1:
                    sf=1/f
                else:
                    sf=f
                self.txt_bshlm_flattening.setText("%.8f" %sf)
                self.cache.flattening=f
                self.cache.axis=a
                self.cache.ellipsoid=name
                self.cache.valid_label=True
            else:
                self.logBshlm("Invalid input label - unable to set ellipsoid data...","red")
                if called_by_index_change: #if called by handler which adds label to list
                    self._handle_system_change=False
                    self.cb_bshlm_system.removeItem(self.cb_bshlm_system.currentIndex())
                    self.cb_bshlm_system.setEditText(mlb)
                    self._handle_system_change=True
                self.txt_bshlm_flattening.setText("")
                self.txt_bshlm_axis.setText("")
                self.cache.valid_label=False
    def doBesselHelmert(self):
        # Check if we need to update data....
        is_custom=self.chb_bshlm_custom_ellipsoid.isChecked()
        self.cache.is_valid=False
        self.logBshlm("",clear=True)
        if is_custom or str(self.cb_bshlm_system.currentText())!=self.cache.mlb:
            self.onBshlmSystemChanged(False)
        if not self.cache.valid_label:
            self.logBshlm("Invalid input label...","red")
            self.clearOutput()
            return
        is_mode1=self.rdobt_bshlm_mode1.isChecked()
        #Get needed input
        mlb=self.cache.mlb
        geo_mlb=self.cache.geo_mlb
        is_geo_in= is_custom or TrLib.IsGeographic(mlb)
        if is_mode1:
            coords,msg=WidgetUtils.getInput(self.input_bshlm,is_geo_in,z_fields=[],angular_unit=self.geo_unit)
            if len(coords)!=4:
                self.logBshlm("Input coordinate %d not OK.\n%s" %(len(coords)+1,msg),"red")
                self.input_bshlm[len(coords)].setFocus()
                self.clearOutput()
                return
            x1,y1,x2,y2=coords
            
        else:
            coords,msg=WidgetUtils.getInput(self.input_bshlm[0:2],is_geo_in,z_fields=[],angular_unit=self.geo_unit)
            if len(coords)!=2:
                self.logBshlm("Station1 coordinates not OK.\n%s" %msg,"red")
                self.input_bshlm[len(coords)].setFocus()
                self.clearOutput()
                return
            input_data,msg=WidgetUtils.getInput(self.input_bshlm_azimuth,True,z_fields=[0],angular_unit=self.geo_unit_derived)
            if len(input_data)!=2:
                self.logBshlm("Input distance and azimuth not OK.\n%s" %msg,"red")
                self.input_bshlm_azimuth[len(input_data)].setFocus()
                self.clearOutput()
                return
            x1,y1=coords
            
            dist,a1=input_data
        a=self.cache.axis
        f=self.cache.flattening
        #end get needed input#
        #transform to geo coords if needed#
        if not is_custom:
            try:
                ct=TrLib.CoordinateTransformation(mlb,geo_mlb)
            except:
                self.logBshlm("Input label not OK!","red")
                self.clearOutput()
                return
            try:
                x1,y1,z=ct.Transform(x1,y1)
            except: 
                msg=""
                err=TrLib.GetLastError()
                if err in ERRORS:
                    msg="\n%s" %ERRORS[err]
                self.logBshlm("Error in transformation of coords for station1"+msg,"red")
                self.clearOutput()
                return
        #display output of first transformation, x1,y1 should now alwyas be in geo-coords#
        WidgetUtils.setOutput([x1,y1],self.output_bshlm_geo[:2],True,z_fields=[],angular_unit=self.geo_unit)
        
        #Now get the other output from bshlm and transformations....
        if is_mode1:
            if not is_custom:
                try: #transform to geographic
                    x2,y2,z=ct.Transform(x2,y2)
                except:
                    msg=""
                    err=TrLib.GetLastError()
                    if err in ERRORS:
                        msg="\n%s" %ERRORS[err]
                    self.logBshlm("Error in transformation of coords for station2"+msg,"red")
                    self.clearOutput()
                    return
            data=TrLib.BesselHelmert(a,f,x1,y1,x2,y2)
            if data[0] is not None:
                a1,a2=data[1:]
                #WidgetUtils.setOutput(data,self.output_bshlm_azimuth,True,z_fields=[0],angular_unit=self.geo_unit_derived)
                self.output_bshlm_azimuth[0].setText("%.3f m" %data[0])
                self.output_bshlm_azimuth[1].setText(translateFromDegrees(data[1],self.geo_unit_derived,precision=1))
                self.output_bshlm_azimuth[2].setText(translateFromDegrees(data[2],self.geo_unit_derived,precision=1))
            else:
                self.message("Error: could not calculate azimuth!")
                self.clearOutput()
                return
        else:
            data=TrLib.InverseBesselHelmert(a,f,x1,y1,a1,dist)
            if data[0] is not None:
                x2,y2,a2=data
                if not is_custom:
                    try:
                        x2_out,y2_out,z2=ct.InverseTransform(x2,y2)
                    except:
                        msg=""
                        err=TrLib.GetLastError()
                        if err in ERRORS:
                            msg="\n%s" %ERRORS[err]
                        self.logBshlm("Error in transformation of coords for station2"+msg,"red")
                        self.clearOutput()
                        return 
                else:
                    x2_out=x2
                    y2_out=y2
                #display result...
                WidgetUtils.setOutput([x2_out,y2_out],self.input_bshlm[2:],is_geo_in,z_fields=[],angular_unit=self.geo_unit)
                self.txt_bshlm_azimuth2.setText(translateFromDegrees(a2,self.geo_unit_derived,precision=1))
            else:
                self.message("Error: could not do inverse Bessel Helmert calculation")
                self.clearOutput()
                return
        #always display ouput in geo field - even if not transformed
        self.cache.a1=a1
        self.cache.a2=a2
        WidgetUtils.setOutput([x2,y2],self.output_bshlm_geo[2:],True,z_fields=[],angular_unit=self.geo_unit)
        self.cache.is_valid=True
        self.cache.mode=int(not is_mode1)
    #called on error	
    def clearOutput(self):
        is_mode1=self.rdobt_bshlm_mode1.isChecked()
        if (is_mode1):
            WidgetUtils.setOutput([],self.output_bshlm_azimuth)
        else:
            WidgetUtils.setOutput([],self.input_bshlm[2:])
            WidgetUtils.setOutput([],self.output_bshlm_azimuth[2:])
        WidgetUtils.setOutput([],self.output_bshlm_geo)
    def logBshlm(self,text,color="black",clear=False):
        self.txt_bshlm_log.setTextColor(QColor(color))
        if (not clear):
            self.txt_bshlm_log.append(text)
        else:
            self.txt_bshlm_log.setText(text)
        self.txt_bshlm_log.ensureCursorVisible()
    #Override methods#
    def handleStdOut(self,text):
        self.logBshlm(text,color="green")
    def handleStdErr(self,text):
        self.logBshlm(text,color="red")
    def handleCallBack(self,text):
        self.logBshlm(text,color="blue")
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
                WidgetUtils.translateAngularField(field,geo_unit,precision=4)
        for field in self.output_bshlm_geo:
            WidgetUtils.translateAngularField(field,geo_unit,precision=4)
    def handleAngularUnitChange(self,geo_unit):
        self.geo_unit_derived=geo_unit
        is_mode1=self.rdobt_bshlm_mode1.isChecked()
        if is_mode1 and self.cache.is_valid and self.cache.mode==0:
            self.txt_bshlm_azimuth1.setText(translateFromDegrees(self.cache.a1,geo_unit,precision=1))
            self.txt_bshlm_azimuth2.setText(translateFromDegrees(self.cache.a2,geo_unit,precision=1))
        else:
            for field in self.derived_angular_output:
                WidgetUtils.translateAngularField(field,geo_unit,precision=3)
    def message(self,text,title="Error"):
        QMessageBox.warning(self,title,text)