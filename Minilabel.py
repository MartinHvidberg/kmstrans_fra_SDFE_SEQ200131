#######################################################
## Some minilabel utility methods
## TODO: fixup dependencies as much functionality has been moved to TrLib.py
## simlk, oct 2012.
## 
#######################################################
SEPS=["E","H","N"]
import sys
from TrLib import SplitMLB,GetParameters
GEO_CODE=2
CRT_CODE=1
PROJ_CODE=0

def GetSysCode(mlb): #TODO - improve this to NO hardcoding!
	try:
		region,proj,datum,hdatum,htype=SplitMLB(mlb)
	except:
		return -1
	if "geo" in proj:
		return GEO_CODE
	if "crt" in proj:
		return CRT_CODE
	return PROJ_CODE


		
def GetPlanarSystems(mlbs):
	systems=[]
	for mlb in mlbs:
		try:
			region,proj,datum,hdatum,htype=SplitMLB(mlb)
		except:
			continue
		if proj=="crt":
			continue
		out=proj
		if len(datum)>0:
			out+="_"+datum
		for param in GetParameters(mlb):
			out+="  "+param
		systems.append(out)
	return systems


def ChangeHeightSystem(mlb,systems):
	try:
		region,proj,datum,hdatum,htype=SplitMLB(mlb)
	except:
		return mlb
	if "crt" in proj:
		return mlb
	
	if not hdatum in systems:
		default=systems[0]
	else:
		i=(systems.index(hdatum)+1) % len(systems)
		default=systems[i]
	out=""
	if region!="":
		out=region+"_"
	out+=proj
	if default in ["E","N"]:
		out+=default+datum
	else:
		out+="H"+datum+"_h_"+default
	for param in GetParameters(mlb):
		out+="  "+param
	return out


