###############
## Various utility functions for e.g. fetching numeric input from QLineEdit fields
## simlk, March 2013
##############
from TrLib_constants import translateToDegrees,translateFromDegrees
DEBUG=False
#a general input converter
#is_angle determines whether input should be considered angles and thus translated - z_fields is a list of those fields that are NOT angles even if some other fields are.
def getInput(fields,is_angle=False,z_fields=[2],angular_unit="dg"):
		coords=[]
		for i in range(len(fields)):
			field=fields[i]
			inp=str(field.text()).replace(" ","").strip()
			try:
				if is_angle and (not i in z_fields):
					inp=translateToDegrees(inp,angular_unit)
					unit="dg"
				else:
					if inp.endswith("km"):
						unit="km"
					else:
						unit="m"
					inp=inp.replace(unit,"")
				inp=float(inp)
				if unit=="km":
					inp*=1e3
			except Exception,msg:
				return coords,str(msg)
			else:
				coords.append(inp)
		return coords,""

#a generel output field setter - flags as above...#
def setOutput(coords,fields,is_angle=False,z_fields=[2],angular_unit="dg",precision=4):
	frmt_metric="{0:."+str(precision)+"f} m"
	if len(coords)==0:
		for field in fields:
			field.clear()
		return
	for i in range(len(fields)):
		if is_angle and (not i in z_fields):
			fields[i].setText("%s" %(translateFromDegrees(coords[i],angular_unit,precision=precision)))
		else:
			#TODO: global precision here
			fields[i].setText(frmt_metric.format(coords[i]))

def translateAngularField(field,geo_unit,precision=4):
	try:
		ang=translateToDegrees(str(field.text()),geo_unit)
	except Exception,msg:
		if DEBUG:
			print repr(msg)
		return
	
	field.setText("%s" %translateFromDegrees(ang,geo_unit,precision=precision))