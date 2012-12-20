#######################################################
## Some minilabel utility methods
## TODO: fixup dependencies as much functionality has been moved to TrLib.py
## simlk, oct 2012.
## 
#######################################################
SEPS=["E","H","N"]
import sys
GEO_CODE=2
CRT_CODE=1
PROJ_CODE=0
class datum(object):
	def __init__(self,desrc,pdatum):
		self.descr=descr.strip()
		self.pdatum=pdatum
		
def SplitMLB(mlb):
	mlb=mlb.split()[0].replace("L","_")
	region=""
	proj=""
	datum=""
	hdatum=""
	htype=""
	sep=""
	if len(mlb)>2:
		if mlb[:2].isupper() and mlb[2]=="_":
			region=mlb[:2]
			mlb=mlb[3:]
	if len(mlb)>1:
		for ssep in SEPS:
			if ssep in mlb:
				sep=ssep
				break
		#no heights#
		if sep=="":
			if "_" in mlb:
				proj,datum=mlb.split("_")
			else:
				proj=mlb
		#heights#
		else:
			proj,datum=mlb.split(sep)
			if "_" in datum:
				if sep!="H":
					raise Exception("Bad minilabel")
				datum,htype,hdatum=datum.split("_")
			else:
				hdatum=sep
	return region,proj,datum,hdatum,htype

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

def FlattenMLB(mlb):
	try:
		region,proj,datum,hdatum,htype=SplitMLB(mlb)
	except:
		return "err"
	if len(datum)>0:
		return proj+"_"+datum
	else:
		return proj
		
def GetPlanarSystems(mlbs):
	systems=[]
	for mlb in mlbs:
		try:
			region,proj,datum,hdatum,htype=SplitMLB(mlb)
		except:
			continue
		if proj=="crt":
			continue
		if len(datum)>0:
			systems.append(proj+"_"+datum)
		else:
			systems.append(proj)
	return systems

def Convert2Geo(mlb,projs):
	try:
		region,proj,datum,hdatum,htype=SplitMLB(mlb)
	except:
		return "err"
	if datum=="":
		if proj in projs:
			datum=projs[proj][1]
		else:
			return "err"
	return "geo"+"_"+datum

def GetEllipsoidData(mlb,datums,ellipsoids):
	try:
		region,proj,datum,hdatum,htype=SplitMLB(mlb)
	except:
		return None
	if datum in datums:
		ellip=datums[datum][0]
		if ellip in ellipsoids:
			return ellipsoids[ellip]
	return None
	
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
	mlb=""
	if region!="":
		mlb=region+"_"
	mlb+=proj
	if default in ["E","N"]:
		mlb+=default+datum
	else:
		mlb+="H"+datum+"_h_"+default
	return mlb

def ParseDefFile(deffile):
	projs={}
	ellips={}
	datums={"E":["","Ellipsoidal heights"],"N":["","Normal heights"]}
	regions={}
	f=open(deffile,"r")
	mode=None
	modes={"def_rgn":regions,"def_prj":projs,"def_dtm":datums,"def_grs":ellips}
	new_modes=modes.keys()
	skiplines={"def_rgn":0,"def_prj":2,"def_dtm":4,"def_grs":0}
	line=Ekms.fgetln(f)
	while len(line)>0:
		sline=line.split()
		if len(sline)==0:
			line=Ekms.fgetln(f)
			continue
		if sline[0][0]=="#" and len(sline[0])>1:
			mlb=sline[0][1:]
			if mlb=="stop":
				mode=None
			elif mlb in new_modes:
				mode=mlb
			elif mode=="def_prj":
				impl_datum=sline[8]
				for i in range(skiplines[mode]-1):
					line=Ekms.fgetln(f)
				line=f.readline()
				i=line.find("(")
				if i!=-1:
					line=line[:i]
				modes["def_prj"][mlb]=[line.strip(),impl_datum]
			elif mode=="def_grs":
				xline=f.readline().split()
				ell_no=int(xline[0])
				axis=float(xline[2])
				flat=float(xline[3])
				modes["def_grs"][mlb]=[ell_no,axis,flat]
			elif mode=="def_dtm":
				xline=f.readline().split()
				ellip=xline[2]
				for i in range(skiplines[mode]-2):
					line=Ekms.fgetln(f)
				line=f.readline()
				modes["def_dtm"][mlb]=[ellip,line.strip()]
				
			elif mode is not None:
				for i in range(skiplines[mode]-1):
					line=Ekms.fgetln(f)
				line=f.readline()
				modes[mode][mlb]=line.strip()
		elif mode=="def_rgn" and len(sline)>2:
			if "STOP" in sline:
				mode=None
				line=Ekms.fgetln(f)
				continue
			modes[mode][sline[0]]=sline[2]
		line=Ekms.fgetln(f)
	f.close()
	return regions,projs,datums,ellips

class MLBDescription(object):
	def __init__(self,region=None,proj=None,datum=None,hdatum=None,htype=None):
		self.region=region
		self.proj=proj
		self.datum=datum
		self.hdatum=hdatum
		self.htype=htype
	def GetDescription(self):
		text=""
		if self.region is not None:
			text+="Region: %s" %self.region
		if self.proj is not None:
			text+="\nProjection: %s" %self.proj
		if self.datum is not None:
			text+="\nDatum: %s" %self.datum
		if self.hdatum is not None:
			text+="\nHeight datum: %s" %self.hdatum
		if self.htype is not None:
			text+="\nHeight type: %s" %self.htype
		return text
	

def GetDescription(mlb,regions,projs,datums):
	try:
		r,p,d,hd,ht=SplitMLB(mlb)
	except:
		return False,MLBDescription("bad minilabel!")
	region=None
	proj=None
	datum=None
	hdatum=None
	htype=None
	if r in regions:
		region=regions[r]
	zone=""
	if "utm" in p:
		zone=p[3:]
		p="utm??"
	if p in projs:
		proj=projs[p][0].replace("??",zone)
		if d=="":
			impl_datum=projs[p][1]
			d=impl_datum
	else:
		return False,MLBDescription("bad minilabel!")
	if d in datums:
		datum=datums[d][1].replace("@","")
	else:
		return False,MLBDescription("bad minilabel!")
	if hd in datums:
		hdatum=datums[hd][1].replace("@","")
	if ht in projs:
		htype=projs[ht][0]
	descr=MLBDescription(region,proj,datum,hdatum,htype)
	return True,descr

if __name__=="__main__":
	r,p,d=ParseDefFile(sys.argv[1])
	ok,text=GetDescription(sys.argv[2],r,p,d)
	if not ok:
		print("Bad minilabel")
	else:
		print text.GetDescription()
	sys.exit()
	
				
	