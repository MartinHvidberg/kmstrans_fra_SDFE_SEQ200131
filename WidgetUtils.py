from TrLib_constants import TranslateToDegrees,TranslateFromDegrees
import TrLib
DEBUG=False
#a general input converter#	
def getInput(fields,mlb_in,z_fields=[2],geo_unit="dg"):
		coords=[]
		is_geo=TrLib.IsGeographic(mlb_in)
		for i in range(len(fields)):
			field=fields[i]
			inp=str(field.text()).replace(" ","")
			try:
				if is_geo and (not i in z_fields):
					inp=TranslateToDegrees(inp,geo_unit)
				else:
					inp=inp.replace("m","")
				inp=float(inp)
			except Exception,msg:
				return coords,str(msg)
			else:
				coords.append(inp)
		return coords,""

#a generel output field setter#
def setOutput(coords,fields,mlb,z_fields=[2],geo_unit="dg"):
	if len(coords)==0:
		for field in fields:
			field.clear()
		return
	is_geo=TrLib.IsGeographic(mlb)
	for i in range(len(fields)):
		if is_geo and (not i in z_fields):
			fields[i].setText("%s" %(TranslateFromDegrees(coords[i],geo_unit)))
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