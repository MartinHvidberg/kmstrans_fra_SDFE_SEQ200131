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
import time
from TrLib_constants import OGRLIB
IS_WINDOWS=sys.platform.startswith("win")
DEBUG=False
IS_PY2EXE=False
CREATE_NO_WINDOW=134217728 #creation flag to not create a 'console' on startup of a subprocess on windows - see msdn documentation... 
PROCESS_TERMINATED=314159265 #Special signal to post when a process is terminated...
if IS_WINDOWS:
	try:
		sys.frozen
	except:
		pass
	else:
		IS_PY2EXE=True
		
		
	


TROGR=None

C_CHAR_P=ctypes.c_char_p
C_INT=ctypes.c_int
LP_c_double=ctypes.POINTER(ctypes.c_double)
LP_c_int=ctypes.POINTER(ctypes.c_int)
#pointer to ogrlib
ogrlib=None

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
		self.input_layers=[]
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
	path=os.path.join(prefix,lib_name)
	#SETUP HEADER#
	try:
		ogrlib=ctypes.cdll.LoadLibrary(path)
		ogrlib.GetOGRDrivers.argtypes=[C_INT,C_INT] #reset reading, is_output
		ogrlib.GetOGRDrivers.restype=C_CHAR_P
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
		print repr(msg),path
		return False
	return True

def KillThreads():
	threads=threading.enumerate()
	for thread in threads:
		if isinstance(thread,WorkerThread):
			thread.kill()
	
#Will return:
#if return_process:
#None, err_msg or valid_process,""
#else
#rc,stdout/stderr
def RunCommand(args,return_process=False):
	if IS_WINDOWS:
		flags=CREATE_NO_WINDOW
	else:
		flags=0
	try:
		#hack to make piping work in all cases:
		# Under Py2EXE if started by double click, or from shell, from python if started as .pyw or .py by click or from shell.
		#previous hack
		#if IS_PY2EXE:
		#	prc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,shell=True,creationflags=win32process.CREATE_NO_WINDOW)
		#else:
		prc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=flags)
	except Exception,msg:
		try:
			#here's the real hack, explicitely open stdin and close again!
			prc=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=flags)
			prc.stdin.close()
		except:
			if return_process:
				return None,repr(msg)
			else:
				return TrLib.TR_ERROR,repr(msg)
	if return_process:
		return prc,""
	else:
		stdout,stderr=prc.communicate()
		return prc.poll(),stdout
	
	
def TestCommand():
	if TROGR is None:
		return TrLib.TR_ERROR,"Command not set"
	else:
		return RunCommand([TROGR,"--version"])

class ReturnValue(object):
	def __init__(self,msg="",rc=0):
		self.msg=msg
		self.rc=rc

def TransformDatasource(options,log_method,post_method):
	#compose command and preanalyze validity#
	args=[]
	if options.log_file is not None:
		args+=['-log',options.log_file]
	if not options.set_projection:
		args+=['-n']
	if options.be_verbose:
		args+=['-v']
	if options.mlb_in is not None:
		args+=['-pin',options.mlb_in]
	if options.driver=="OGR":
		if options.format_out is not None:
			args+= ['-f',options.format_out]
	elif len(options.input_layers)>0:
		return False,"Input layers can only be specified for OGR datasources"
	elif options.driver=="TEXT":
		if os.path.isdir(options.ds_in):
			return False,"For the 'TEXT' driver you can batch several files using the * expansion char."
		args+=['-drv','TEXT']
		if options.col_x is not None:
			args+=['-x','%d' %options.col_x]
		if options.col_y is not None:
			args+=['-y', '%d' %options.col_y]
		if options.col_z is not None:
			args+=['-z', '%d' %options.col_z]
		if options.sep_char is not None:
			args+=['-sep', options.sep_char]
	elif options.driver=="DSFL":
		if os.path.isdir(options.ds_in):
			return False,"For the 'DSFL' driver you can batch several files using the * expansion char."
		args+=['-drv', 'DSFL']
	elif options.driver=="KMS":
		if os.path.isdir(options.ds_in):
			return False,"For the 'KMS' driver you can batch several files using the * expansion char."
		args+=['-drv','KMS']
		#TODO: implement extra options for KMS-driver#
	files=glob.glob(options.ds_in)
	if len(files)==0:
		files=[options.ds_in]  #OK so we assume its not a file - could be a db or url.... TODO: see if WFS or similar driver is specified....
	if len(files)>1: 
		if not os.path.isdir(options.ds_out):
			return False,"More than one input datasource specified - output datasource must be a directory."
		if len(options.input_layers)>0:
			return False,"Input layers can only be specified for a single OGR datasource."
		
	#Really start a thread here#
	args=[TROGR]+args+[options.mlb_out]
	if len(files)>1 and os.path.isdir(options.ds_out):
		files_out=[os.path.join(options.ds_out,fname) for fname in files]
	else:
		files_out=[options.ds_out]
	options.output_files=files_out
	thread=WorkerThread(log_method,post_method,args,files,files_out,options.input_layers)
	thread.start()
	return True,"Thread started..."

class WorkerThread(threading.Thread):
	def __init__(self,log_method,post_method,args,files_in,files_out,layers):
		threading.Thread.__init__(self)
		self.log_method=log_method
		self.post_method=post_method
		self.files_in=files_in
		self.files_out=files_out
		self.args=args
		self.layers=layers
		self.prc=None
		self.kill_flag=threading.Event()
	def kill(self):
		self.kill_flag.set()
		if self.prc is not None:
			self.prc.terminate()
			self.prc=None
	def run(self):
		n_errs=0
		rc=0
		last_err=0
		done=0
		self.kill_flag.clear()
		for f_in,f_out in zip(self.files_in,self.files_out):
			#Append -a to args....
			if done==1:
				if ("-log") in args:
					self.args.insert(1,"-a")
			args=self.args+[f_out,f_in]+self.layers
			self.log_method(repr(args))
			self.prc,msg=RunCommand(args,True)
			if self.prc is None:
				self.log_method(msg)
				self.post_method(1)
				return
			last_log=time.clock()
			while (not self.kill_flag.isSet()) and self.prc.poll() is None: #short circuit when kill flag isSet -> prc=None
				#read input - consider using prc.communicate as this might deadlock due to other os processes
				#but then again - its the only callback mechanism for reporting progress thats really available in this setup...
				#time.sleep(0.1)
				#now=time.clock()
				#if (now-last_log)>2:
				#	self.log_method(".")
				#	last_log=now
				try:
					line=self.prc.stdout.readline().rstrip()
				except:
					pass
				else:
					self.log_method(line)
			#process was killed
			if (self.kill_flag.isSet()):
				self.post_method(PROCESS_TERMINATED) #a special termination signal...
				return
			#stdout,stderr=prc.communicate()
			#self.log_method(stdout.strip())
			rc=self.prc.poll()	
			if rc!=0:
				last_err=rc
				n_errs+=1
			if n_errs>10:
				self.log_method("Many errors, aborting....")
				self.post_method(last_err)
				return
			done+=1
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

def GetOGRFormats(is_output=True):
	ogrlib.GetOGRDrivers(1,0)
	drivers=[]
	drv=ogrlib.GetOGRDrivers(0,1)
	while drv is not None:
		drivers.append(drv)
		drv=ogrlib.GetOGRDrivers(0,int(is_output)) #should make a copy into python managed memory.... 1 signals output
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
	
	