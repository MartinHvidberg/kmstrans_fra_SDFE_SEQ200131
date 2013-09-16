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
	TRLIB="libtr.dll"
	LIBTRUI="libtrui.dll"
elif "darwin" in sys.platform:
	TRLIB="libtr.dylib"
	LIBTRUI="libtrui.dylib"
else:
	TRLIB="libtr.so"
	LIBTRUI="libtrui.so"
TROGRNAME="trogr"

#CONSTANTS RELEVANT TO KMSTRLIB
#A MAPPING FROM SPECIAL DATUMS TO ALLOWED H_SYSTEMS, THE REGION MAP SHOULD BE CONSIDERED AS A DEFAULT,
DATUM_ALLOWED_H_SYSTEMS={"feh10":["E","fcsvr10","_"],"detrs89":["E","dhhn92","_"]}
#DK
SYSTEMS_DK=["utm32Hetrs89_h_dvr90","utm33Hetrs89_h_dvr90",
"geoHetrs89_h_dvr90","crt_etrs89","dktm1H_h_dvr90","dktm2H_h_dvr90","dktm3H_h_dvr90","dktm4H_h_dvr90",
"utm32Hed50_h_dvr90","fcsH_h_fcsvr10","kp2000jH_h_dvr90","kp2000sH_h_dvr90","kp2000bH_h_dvr90","s34jH_h_dvr90","s34sH_h_dvr90","s34bH_h_dvr90"]
H_SYSTEMS_DK=["E","dvr90","dnn","_"]
#Fehmarn
SYSTEMS_FEHMARN=["fcsH_h_fcsvr10","geoHfeh10_h_fcsvr10","crt_feh10","DE_utm32Hdetrs89_h_dhhn92","DE_geoHdetrs89_h_dhhn92","DE_crt_detrs89",
"DK_utm32Hetrs89_h_dvr90","DK_utm33Hetrs89_h_dvr90","DK_geoHetrs89_h_dvr90","DK_crt_etrs89"]
H_SYSTEMS_FEHMARN=["E","dvr90","dnn","_"]
#FO
SYSTEMS_FO=["fotmH_h_fvr09","utm29Hetrs89_h_fvr09","geoHetrs89_h_fvr09","fkeH_h_fvr09","fk89H_h_fvr09"]
H_SYSTEMS_FO=["E","fvr09","foldmsl","_"]
#GR
SYSTEMS_GR=["utm22Ngr96","utm24Ngr96","utm26Ngr96","geoNgr96","crt_gr96","mrc0Ngr96","utm22Nqornoq","geoNqornoq"]
H_SYSTEMS_GR=["E","N","_"]
#WORLD
SYSTEMS_WORLD=["webmrcE","mrc0Ewgs84","geoEwgs84","crt_wgs84","npstgEwgs84"]
H_SYSTEMS_WORLD=["E","N","_"]
#INIT COORDS IN FIRST 'DEFAULT' SYSTEM IN LIST
INIT_DK=[615923.206,6115220.6360,0]
INIT_FEHMARN=[990000.0,6058000.0,0]
INIT_FO=[200000.000 ,876910.289,0]
INIT_GR=[451351.736,7114111.319,0]
INIT_WORLD=[1204476.890, 7394929.797, 0]
#REGIONS
REGION_DK="DK"
REGION_FEHMARN="FB"
REGION_FO="FO"
REGION_GR="GR"
REGION_WORLD="WORLD"
REGIONS={
REGION_DK:[SYSTEMS_DK,INIT_DK,"Denmark"],
REGION_FEHMARN:[SYSTEMS_FEHMARN,INIT_FEHMARN,"Fehmarn"],
REGION_FO:[SYSTEMS_FO,INIT_FO,"Faroe Islands"],
REGION_GR:[SYSTEMS_GR,INIT_GR,"Greenland"],
REGION_WORLD:[SYSTEMS_WORLD,INIT_WORLD,"World"]
}
H_SYSTEMS={REGION_DK:H_SYSTEMS_DK,REGION_FO:H_SYSTEMS_FO,REGION_GR:H_SYSTEMS_GR,REGION_WORLD:H_SYSTEMS_WORLD,REGION_FEHMARN:H_SYSTEMS_FEHMARN}
#ERRORS - see s_status.h (other error types irrelevant here)
ERRORS={
-1:"Inaccurate transformation",
-2:"Tolerance exceeded",
-3:"Boundary exceeded (serious)",
-4:"No geoid - illegal transformation",
-5:"Illegal transformation",
-6:"Program / system error",
-7:"Illegal height transformation",
-100:"Table boundary exceeded (serious)"
}

#ANGULAR UNITS
ANGULAR_UNIT_DEGREES="dg"
ANGULAR_UNIT_RADIANS="rad"
ANGULAR_UNIT_NT="nt"
ANGULAR_UNIT_SX="sx"
ANGULAR_UNITS=[ANGULAR_UNIT_DEGREES,ANGULAR_UNIT_RADIANS,ANGULAR_UNIT_NT,ANGULAR_UNIT_SX]
LOGR=7
LOGM=3
LOGS=2
LOGD=5
def GetFrmt(geo_unit,precision):
	if geo_unit==ANGULAR_UNIT_RADIANS:
		return "{0:."+str(LOGR+precision)+"f}"
	if geo_unit==ANGULAR_UNIT_NT:
		return "{0:0"+str(LOGM+precision+3)+"."+str(LOGM+precision)+"f}"
	if geo_unit==ANGULAR_UNIT_SX:
		return "{0:02d} {1:0"+str(LOGS+precision+3)+"."+str(LOGS+precision)+"f}"
	return "{0:."+str(LOGD+precision)+"f}"

#Translate from dg to other geo units
#DONE: avoid round up to 60 seconds/minutes - handling negative input ok...
def TranslateFromDegrees(x,geo_unit, precision=4):
	frmt=GetFrmt(geo_unit,precision)
	if geo_unit==ANGULAR_UNIT_RADIANS:
		return frmt.format(x*pi/180.0)+" "+geo_unit
	if geo_unit==ANGULAR_UNIT_NT or geo_unit==ANGULAR_UNIT_SX:
		sign=""
		dec=""
		if x<0:
			sign="-"
			x=abs(x)
		dg=floor(x)
		m=(x-dg)*60.0 #between 0 and 1 - thus output below 60
		if geo_unit==ANGULAR_UNIT_NT:
			if (60.0-m)<10**(-precision-LOGM):
				m=0.0
				dg=round(x)
			dec=frmt.format(m)
		else:
			if (60.0-m)<10**(-precision-LOGM): #double check this logic
				m=0.0
				s=0.0
				dg=round(x)
			else:	
				s=(m-floor(m))*60 #between 0 and 1 - thus output below 60
				if (60.0-s)<10**(-precision-LOGS):
					m=int(round(m))
					s=0.0
					if (m==60):
						m=0.0
						dg=round(x)
			dec=frmt.format(int(m),s)
		out=sign
		if (dg>0):
			out+="{0:d} ".format(int(dg))
		out+=dec+" "+geo_unit
		return out
	return frmt.format(x)+" "+geo_unit

def TranslateToDegrees(x,geo_unit): #geo_unit acts as a default if unit is not specified...
	for unit in ANGULAR_UNITS:
		if unit in x:
			geo_unit=unit
			break
	x=x.replace(geo_unit,"").replace(" ","").strip()
	x=x.replace(",",".")
	if geo_unit==ANGULAR_UNIT_RADIANS:
		return float(x)*180.0/pi
	if geo_unit==ANGULAR_UNIT_NT or  geo_unit==ANGULAR_UNIT_SX:
		#TODO: taking care of sign
		sign=1
		if x[0]=="-":
			sign=-1
			x=x[1:]
		elif x[0]=="+":
			x=x[1:]
		index_dot=x.find(".")
		if index_dot==-1:
			index_dot=len(x)
		if geo_unit==ANGULAR_UNIT_NT:
			index_m=max(0,index_dot-2)
			m=float(x[index_m:])
			if (m>60):
				raise ValueError("Minutes must be between 0 and 60")
			if index_m>0:
				dg=int(x[:index_m])
			else:
				dg=0
			return sign*(dg+m/60.0)
		else: 
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
			return sign*(dg+m/60.0+s/3600.0)
	return float(x)
