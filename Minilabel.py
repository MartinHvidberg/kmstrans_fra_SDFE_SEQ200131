#######################################################
## Some minilabel utility methods
## TODO: fixup dependencies as much functionality has been moved to TrLib.py - DONE
## simlk, oct 2012.
## 
#######################################################
import sys
from TrLib import SplitMLB,GetParameters,DescribeProjection,LabelException

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

def GetImplicitDatum(mlb_prj):
	descr_prj,impl_dtm=DescribeProjection(mlb_prj)
	if descr_prj is None or len(impl_dtm)==0:
		raise LabelException("Label not OK!")
	return impl_dtm

def ChangeHeightSystem(mlb,default_systems, allowed_systems=None):
	try:
		region,proj,datum,hdatum,htype=SplitMLB(mlb)
	except:
		return mlb
	if "crt" in proj:
		return mlb
	if len(datum)==0:
		sdtm=GetImplicitDatum(proj)
	else:
		sdtm=datum
	if allowed_systems is not None and sdtm in allowed_systems:
		systems=allowed_systems[sdtm]
	else:
		systems=default_systems
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


