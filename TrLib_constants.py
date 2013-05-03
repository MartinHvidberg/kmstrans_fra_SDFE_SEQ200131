"""/*
* Copyright (c) 2011, National Survey and Cadastre, Denmark
* (Kort- og Matrikelstyrelsen), kms@kms.dk
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 */
 """
from math import pi,floor
import sys
IS_WINDOWS=sys.platform.startswith("win")
#LIBRARYNAMES
#PATH TO TRLIB, OGRLIB#
if IS_WINDOWS:
	TRLIB="trlib_ui.dll"
	OGRLIB="libtrogr.dll"
elif "darwin" in sys.platform:
	TRLIB="trlib_ui.dylib"
	OGRLIB="libtrogr.dylib"
else:
	TRLIB="trlib_ui.so"
	OGRLIB="libtrogr.so"
TROGRNAME="trogr"

#CONSTANTS RELEVANT TO KMSTRLIB
#A MAPPING FROM SPECIAL DATUMS TO ALLOWED H_SYSTEMS, THE REGION MAP SHOULD BE CONSIDERED AS A DEFAULT,
DATUM_ALLOWED_H_SYSTEMS={"feh10":["E","fcsvr10"],"detrs89":["E","dhhn92"]}
#DK
SYSTEMS_DK=["utm32Hetrs89_h_dvr90","utm33Hetrs89_h_dvr90",
"geoHetrs89_h_dvr90","crt_etrs89","dktm1H_h_dvr90","dktm2H_h_dvr90","dktm3H_h_dvr90","dktm4H_h_dvr90",
"utm32Hed50_h_dvr90","fcsH_h_fcsvr10"]
H_SYSTEMS_DK=["E","dvr90","dnn"]
#FO
SYSTEMS_FO=["fotmH_h_fvr09","utm29Hetrs89_h_fvr09","geoHetrs89_h_fvr09","fkeH_h_fvr09","fk89H_h_fvr09"]
H_SYSTEMS_FO=["E","fvr09","foldmsl"]
#GR
SYSTEMS_GR=["utm22Ngr96","utm24Ngr96","utm26Ngr96","geoNgr96","crt_gr96","mrc0Ngr96","utm22Nqornoq","geoNqornoq"]
H_SYSTEMS_GR=["E","N","msl"]
#WORLD
SYSTEMS_WORLD=["webmrcE","mrc0Ewgs84","geoEwgs84","crt_wgs84","npstgEwgs84"]
H_SYSTEMS_WORLD=["E","N","msl"]
#INIT COORDS IN FIRST 'DEFAULT' SYSTEM IN LIST
INIT_DK=[615923.206,6115220.6360,0]
INIT_FO=[200000.000 ,876910.289,0]
INIT_GR=[451351.736,7114111.319,0]
INIT_WORLD=[1204476.890, 7394929.797, 0]
#REGIONS
REGION_DK="DK"
REGION_FO="FO"
REGION_GR="GR"
REGION_WORLD="WORLD"
REGIONS={
REGION_DK:[SYSTEMS_DK,INIT_DK,"Denmark"],
REGION_FO:[SYSTEMS_FO,INIT_FO,"Faroe Islands"],
REGION_GR:[SYSTEMS_GR,INIT_GR,"Greenland"],
REGION_WORLD:[SYSTEMS_WORLD,INIT_WORLD,"World"]
}
H_SYSTEMS={REGION_DK:H_SYSTEMS_DK,REGION_FO:H_SYSTEMS_FO,REGION_GR:H_SYSTEMS_GR,REGION_WORLD:H_SYSTEMS_WORLD}
#ERRORS
ERRORS={
-1:"Inaccurate transformation",
-2:"Tolerance exceeded",
-3:"Boundary exceeded",
-5:"Illegal transformation",
-100:"Table boundary exceeded"
}

#ANGULAR UNITS
ANGULAR_UNIT_DEGREES="dg"
ANGULAR_UNIT_RADIANS="rad"
ANGULAR_UNIT_NT="nt"
ANGULAR_UNIT_SX="sx"
ANGULAR_UNITS=[ANGULAR_UNIT_DEGREES,ANGULAR_UNIT_RADIANS,ANGULAR_UNIT_NT,ANGULAR_UNIT_SX]
#Translate from dg to other geo units
#DONE: avoid round up to 60 seconds/minutes
def TranslateFromDegrees(x,geo_unit):
	if geo_unit==ANGULAR_UNIT_RADIANS:
		return "{0:.9f} {1}".format(x*pi/180.0,ANGULAR_UNIT_RADIANS)
	if geo_unit==ANGULAR_UNIT_NT:
		dg=floor(x)
		m=(x-dg)*60.0 #between 0 and 1 - thus output below 60
		if (60.0-m)<1e-6:
			m=0.0
			dg=round(x)
		return "{0:d} {1:09.6f} {2}".format(int(dg),m,ANGULAR_UNIT_NT)
	if geo_unit==ANGULAR_UNIT_SX:
		dg=floor(x)
		m=(x-dg)*60.0
		if (60.0-m)<1e-5/60.0:
			m=0.0
			s=0.0
			dg=round(x)
		else:	
			s=(m-floor(m))*60 #between 0 and 1 - thus output below 60
		return "{0:d} {1:02d} {2:08.5f} {3}".format(int(dg),int(m),s,ANGULAR_UNIT_SX)
	return "{0:.8f} dg".format(x)

def TranslateToDegrees(x,geo_unit): #geo_unit acts as a default if unit is not specified...
	for unit in ANGULAR_UNITS:
		if unit in x:
			geo_unit=unit
			break
	x=x.replace(geo_unit,"").replace(" ","")
	x=x.replace(",",".")
	index_dot=x.find(".")
	if index_dot==-1:
		index_dot=len(x)
	if geo_unit==ANGULAR_UNIT_RADIANS:
		return float(x)*180.0/pi
	if geo_unit==ANGULAR_UNIT_NT:
		index_m=max(0,index_dot-2)
		m=float(x[index_m:])
		if (m>60):
			raise ValueError("Minutes must be between 0 and 60")
		if index_m>0:
			dg=int(x[:index_m])
		else:
			dg=0
		return dg+m/60.0
	if geo_unit==ANGULAR_UNIT_SX:
		index_s=max(0,index_dot-2)
		s=float(x[index_s:])
		m=0
		dg=0
		if (s>60):
			raise ValueError("Seconds must be between 0 and 60")
		if index_s>0:
			index_m=max(0,index_s-2)
			m=int(x[index_m:index_s])
			if (m>60):
				raise ValueError("Minutes must be between 0 and 60")
			if index_m>0:
				dg=int(x[:index_m])
		return dg+m/60.0+s/3600.0
	return float(x)
