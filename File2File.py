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
import ctypes
import os,sys
import TrLib
import subprocess
import glob
import threading
from TrLib_constants import OGRLIB
IS_WINDOWS=sys.platform.startswith("win")
DEBUG=False
IS_PY2EXE=False

if IS_WINDOWS:
	try:
		sys.frozen
	except:
		pass
	else:
		IS_PY2EXE=True
		import win32process
	


TROGR=None

C_CHAR_P=ctypes.c_char_p
C_INT=ctypes.c_int
LP_c_double=ctypes.POINTER(ctypes.c_double)
LP_c_int=ctypes.POINTER(ctypes.c_int)

class F2F_Settings(object):
	def __init__(self):
		self.driver="OGR"
		self.format_out=None
		self.mlb_in=None
		self.mlb_out=None
		self.col_x=None
		self.col_y=None
		self.col_z=None
		self.set_projection=True
		self.be_verbose=False
		self.ds_in=None
		self.ds_out=None
		self.input_layers={}
		self.accepted=False
		self.sep_char=None
		self.log_file=None
		self.is_done=False
		self.is_started=False
		self.output_files=[]
		


def SetCommand(prog_path):
	global TROGR
	TROGR=prog_path


#LOAD LIBRARY#
def InitOGR(prefix,lib_name=OGRLIB):
	global ogrlib
	#SETUP HEADER#
	try:
		path=os.path.join(prefix,lib_name)
		ogrlib=ctypes.cdll.LoadLibrary(path)
		ogrlib.GetOGRDrivers.argtypes=[C_CHAR_P]
		ogrlib.GetOGRDrivers.restype=None
		ogrlib.GetLayer.restype=ctypes.c_void_p
		ogrlib.GetLayer.argtypes=[ctypes.c_void_p,C_INT]
		ogrlib.GetLayerCount.restype=C_INT
		ogrlib.GetLayerCount.argtypes=[ctypes.c_void_p]
		ogrlib.GetLayerName.restype=C_CHAR_P
		ogrlib.GetLayerName.argtypes=[ctypes.c_void_p]
		ogrlib.GetNextGeometry.restype=ctypes.c_void_p
		ogrlib.GetNextGeometry.argtypes=[ctypes.c_void_p,LP_c_int]
		ogrlib.Close.restype=None
		ogrlib.Close.argtypes=[ctypes.c_void_p]
		ogrlib.Open.restype=ctypes.c_void_p
		ogrlib.Open.argtypes=[C_CHAR_P]
		ogrlib.GetCoords.argtypes=[ctypes.c_void_p,LP_c_double,LP_c_double,C_INT]
		ogrlib.GetCoords.restype=None
	#END HEADER#
	except Exception,msg:
		print msg,path
		return False
	return True
	

def RunCommand(args,post_method=None):
	if post_method is not None:
		post_method(repr(args))
	try:
		#hack to make piping work under py2exe
		if IS_PY2EXE:
			prc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,shell=True,creationflags=win32process.CREATE_NO_WINDOW)
		else:
			prc=prc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
	except Exception,msg:
		if post_method is not None:
			post_method(repr(msg))
		return TrLib.TR_ERROR
	while prc.poll() is None:
		#read input
		line=prc.stdout.readline()
		if post_method is not None:
			post_method(line.rstrip())
	post_method(prc.stdout.read())
	return prc.poll()
	
def TestCommand(post_method):
	if TROGR is None:
		return TrLib.TR_ERROR
	else:
		return RunCommand([TROGR,"--version"],post_method)

class ReturnValue(object):
	def __init__(self,msg="",rc=0):
		self.msg=msg
		self.rc=rc

def TransformDatasource(options,log_method,post_method):
	#compose command and preanalyze validity#
	args=[]
	if options.log_file is not None:
		args+=['-l',options.log_file]
	if not options.set_projection:
		args+=['-n']
	if options.be_verbose:
		args+=['-v']
	if options.mlb_in is not None:
		args+=['-p',options.mlb_in]
	if options.driver=="OGR":
		if options.format_out is not None:
			args+= ['-f',options.format_out]
	elif options.driver=="TEXT":
		if os.path.isdir(options.ds_in):
			return False,"For the 'TEXT' driver you can batch several files using the * expansion char."
		args+=['-d','TEXT']
		if options.col_x is not None:
			args+=['-x','%d' %options.col_x]
		if options.col_y is not None:
			args+=['-y', '%d' %options.col_y]
		if options.col_z is not None:
			args+=['-z', '%d' %options.col_z]
		if options.sep_char is not None:
			args+=['-s', options.sep_char]
	elif options.driver=="DSFL":
		if os.path.isdir(options.ds_in):
			return False,"For the 'DSFL' driver you can batch several files using the * expansion char."
		args+=['-d', 'DSFL']
	elif options.driver=="KMS":
		if os.path.isdir(options.ds_in):
			return False,"For the 'KMS' driver you can batch several files using the * expansion char."
		args+=['-d','KMS']
		#TODO: implement extra options for KMS-driver#
	files=glob.glob(options.ds_in)
	if len(files)>1 and not os.path.isdir(options.ds_out):
		return False,"More than one input datasource specified - output datasource must be a directory."
	#Really start a thread here#
	args=[TROGR]+args+[options.mlb_out]
	if len(files)>1 and os.path.isdir(options.ds_out):
		files_out=[os.path.join(options.ds_out,fname) for fname in files]
	else:
		files_out=[options.ds_out]
	options.output_files=files_out
	thread=WorkerThread(log_method,post_method,args,files,files_out)
	thread.start()
	return True,"Thread started..."

class WorkerThread(threading.Thread):
	def __init__(self,log_method,post_method,args,files_in,files_out):
		threading.Thread.__init__(self)
		self.log_method=log_method
		self.post_method=post_method
		self.files_in=files_in
		self.files_out=files_out
		self.args=args
	def run(self):
		n_errs=0
		for f_in,f_out in zip(self.files_in,self.files_out):
			args=self.args+[f_out,f_in]
			rc=RunCommand(args,self.log_method)
			if rc!=0:
				n_errs+=1
			if n_errs>10:
				self.log_method("Many errors, aborting....")
				self.post_method(rc)
				return
		self.post_method(rc)
	
			
		
	
		
		
			

def TransformDSFL(inname,outname,mlb_out):
	msg_str=" "*1024
	rc=palib.TransformDSFL(inname,outname,mlb_out,msg_str)
	msg_str=msg_str.replace("\0","").strip()
	return ReturnValue(msg_str,rc)

def TransformText(inname,outname,mlb_in,mlb_out,post_msg,post_done):
	args=" -d TEXT -p %s %s %s %s" %(mlb_in,mlb_out,outname,inname)
	rc=RunCommand(TROGR+args,post_msg)
	post_done(rc)
	return ReturnValue("hej",rc)

def TransformOGR(inname,outname,mlb_in,mlb_out,drv_out):
	rc=ogrlib.TransformOGR(inname,outname,mlb_in,mlb_out,drv_out,None,0)
	msg=ogrlib.GetMsgLog()
	return ReturnValue(msg,rc)

def GetOGRFormats():
	drivers=" "*2048
	ogrlib.GetOGRDrivers(drivers)
	drivers=drivers.replace("\0","").strip().splitlines()
	return drivers

def GetLayer(ds,layer_num=0):
	return ogrlib.GetLayer(ds,layer_num)

def GetNextGeometry(hLayer):
	nump=ctypes.c_int(0)
	geom=ogrlib.GetNextGeometry(hLayer,ctypes.byref(nump))
	return geom,nump.value

def Close(ds):
	ogrlib.Close(ds)

def Open(inname):
	return ogrlib.Open(inname)

def GetCoords(geom,n):
	arr=ctypes.c_double*n
	x=arr()
	y=arr()
	ogrlib.GetCoords(geom,ctypes.cast(x,LP_c_double),ctypes.cast(y,LP_c_double),n)
	return zip(x,y)
	
def GetLines(inname):
	ds=Open(inname)
	lines=[]
	if ds is None:
		return []
	layer=GetLayer(ds,0)
	if layer is None:
		
		Close(ds)
		return []
	geom,n=GetNextGeometry(layer)
	i=0
	while geom!=0 and geom is not None:
		i+=1
		if n==0:
			if DEBUG:
				print "No points, feature %d" %i
			
		else:
			lines.append(GetCoords(geom,n))
		geom,n=GetNextGeometry(layer)
	if DEBUG:
		print geom,geom==0,geom==None
	Close(ds)
	return lines
		
def GetLayerNames(ds):
	layers=[]
	if ds is not None:
		n=ogrlib.GetLayerCount(ds)
		for i in range(n):
			layers.append(ogrlib.GetLayerName(ogrlib.GetLayer(ds,i)))
	return layers


#TODO: Improve KMS 'driver'#
def TransformKMS(file_in,file_out,label_in_file,mlb_in,mlb_out):
	if not TrLib.IS_INIT:
		return ReturnValue("TrLib not initialised",1)
	msg=""
	try:
		f=open(file_in,"r")
	except:
		return ReturnValue("Could not open input file",1)
	stations,mlb=Ekms.GetCRD(f,label_in_file)
	f.close()
	if label_in_file and mlb is None:
		return ReturnValue("Minilabel could not be found in file!",1)
	if len(stations)==0:
		return ReturnValue("No stations found in input file",1)
	if label_in_file:
		mlb_in=mlb
	msg+="Found %d stations. Input label is: %s\n" %(len(stations),mlb_in)
	crd=stations.values()
	try:
		ct=TrLib.CoordinateTransformation(mlb_in,mlb_out)
	except:
		return ReturnValue("Could not open transformation %s->%s" %(mlb_in,mlb_out),1)
	crd_out=ct.Transform(crd)
	ct.Close()
	keys=stations.keys()
	try:
		f=open(file_out,"w")
	except:
		return ReturnValue("Could not open input file",1)
	f.write("#%s\n" %mlb_out)
	is_geo=TrLib.IsGeographic(mlb_out)
	if is_geo:
		planar_unit="dg"
	else:
		planar_unit="m"
	for i in range(len(keys)):
		station=keys[i]
		xyz=crd_out[i]
		if len(xyz)==2:
			f.write("%s  %.5f %s  %.5f %s\n" %(station,xyz[0],planar_unit,xyz[1],planar_unit))
		elif len(xyz)==3:
			f.write("%s  %.5f %s  %.5f %s  %.4f m\n" %(station,xyz[0],planar_unit,xyz[1],planar_unit,xyz[2]))
	f.close()
	return ReturnValue(msg,TrLib.TR_OK)
	
	



if __name__=="__main__":
	f=GetOGRFormats()
	print repr(f)
	
	