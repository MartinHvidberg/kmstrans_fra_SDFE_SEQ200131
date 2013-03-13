###############
## Various utility functions for e.g. fetching numeric input from QLineEdit fields
## simlk, March 2013
##############
from TrLib_constants import TranslateToDegrees,TranslateFromDegrees
import TrLib
DEBUG=False
#a general input converter
#is_angle determines whether input should be considered angles and thus translated - z_fields is a list of those fields that are NOT angles even if some other fields are.
def getInput(fields,is_angle=False,z_fields=[2],angular_unit="dg"):
		coords=[]
		for i in range(len(fields)):
			field=fields[i]
			inp=str(field.text()).replace(" ","")
			try:
				if is_angle and (not i in z_fields):
					inp=TranslateToDegrees(inp,angular_unit)
				else:
					inp=inp.replace("m","")
				inp=float(inp)
			except Exception,msg:
				return coords,str(msg)
			else:
				coords.append(inp)
		return coords,""

#a generel output field setter - flags as above...#
def setOutput(coords,fields,is_angle=False,z_fields=[2],angular_unit="dg"):
	if len(coords)==0:
		for field in fields:
			field.clear()
		return
	for i in range(len(fields)):
		if is_angle and (not i in z_fields):
			fields[i].setText("%s" %(TranslateFromDegrees(coords[i],angular_unit)))
		else:
			#TODO: global precision here
			fields[i].setText("%.4f m" %coords[i])

def translateAngularField(field,geo_unit):
	try:
		ang=TranslateToDegrees(str(field.text()),geo_unit)
	except Exception,msg:
		if DEBUG:
			print repr(msg)
		return
	
	field.setText("%s" %TranslateFromDegrees(ang,geo_unit))