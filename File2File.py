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
from OGR_drivers import *
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
#Ctypes
C_CHAR_P=ctypes.c_char_p
C_INT=ctypes.c_int
LP_c_double=ctypes.POINTER(ctypes.c_double)
LP_c_int=ctypes.POINTER(ctypes.c_int)
#pointers to ogrlib and the TROGR program
ogrlib=None
TROGR=None

class F2F_Settings(object):
	def __init__(self):
		self.driver="OGR"
		self.format_out=None
		self.mlb_in=None
		self.mlb_out=None
		self.col_x=None
		self.col_y=None
		self.col_z=None
		self.n_decimals=4
		self.flip_xy=False
		self.set_projection=True
		self.be_verbose=False
		self.ds_in=None
		self.ds_out=None
		self.input_layers=[]
		self.accepted=False
		self.sep_char=None
		self.comments=None
		self.copy_bad_lines=False
		self.units_in_output=False
		self.output_geo_unit="dg"
		self.log_file=None
		self.is_done=False
		self.is_started=False
		self.output_files=[]
		#serialized state of settings dialog
		self.saved_state_chbs=[] #check boxes
		self.saved_state_rdbs=[] #radio buttons - mutually exclusive
		self.saved_state_text=[] # text fields (lineEdit)
		self.saved_state_spbs=[] #spin boxes
		


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
	except Exception,e:
		#print repr(msg),path
		return False,repr(e)
	return True,""

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
	
#Some hardcoded options for TROGR below#
#Update to reflect changes in main.c#

def TestCommand():
	if TROGR is None:
		return TrLib.TR_ERROR,"Command not set"
	else:
		return RunCommand([TROGR,"--version"])

def ListFormats():
	if TROGR is None:
		return "trogr not available..."
	else:
		ok,text=RunCommand([TROGR,"--formats"])
	return text

def TransformDatasource(options,log_method,post_method):
	#compose command and preanalyze validity#
	args=[]
	if options.log_file is not None:
		#encode just in time#
		args+=['-log',options.log_file.encode(sys.getfilesystemencoding())]
	if not options.set_projection:
		args+=['-nop']
	if options.be_verbose:
		args+=['-verb']
	if options.mlb_in is not None:
		args+=['-pin',options.mlb_in]
	if options.driver=="OGR":
		if options.format_out is not None:
			frmt_out=options.format_out
			if frmt_out in OGR_LONG_TO_SHORT:
				frmt_out,dco,lco=OGR_LONG_TO_SHORT[frmt_out]
			args+= ['-of',frmt_out]
			if len(dco)>0:
				args+=['-dco',dco]
			if len(lco)>0:
				args+=['-lco',lco]
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
		if options.flip_xy:
			args+=['-flipxy']
		if options.units_in_output:
			args+=['-ounits']
		if options.comments is not None:
			args+=['-comments',options.comments]
		
	elif options.driver=="DSFL":
		if os.path.isdir(options.ds_in):
			return False,"For the 'DSFL' driver you can batch several files using the * expansion char."
		args+=['-drv', 'DSFL']
	elif options.driver=="KMS":
		if os.path.isdir(options.ds_in):
			return False,"For the 'KMS' driver you can batch several files using the * expansion char."
		args+=['-drv','KMS']
		#TODO: implement extra options for KMS-driver#
	if options.driver=="KMS" or options.driver=="TEXT":
		if options.output_geo_unit=="sx":
			args+=['-sx']
		elif options.output_geo_unit=="nt":
			args+=['-nt']
		elif options.output_geo_unit=="rad":
			args+=['-rad']
		if options.copy_bad_lines:
			args+=['-cpbad']
		args+=['-prc','%d'%options.n_decimals]
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
					self.args.insert(1,"-alog")
			#encode in file system encoding - just in time #
			f_out=f_out.encode(sys.getfilesystemencoding())
			f_in=f_in.encode(sys.getfilesystemencoding())
			args=self.args+[f_out,f_in]+self.layers
			self.log_method(repr(args))
			self.prc,msg=RunCommand(args,True)
			if self.prc is None:
				self.log_method(msg)
				self.post_method(1)
				return
			last_log=time.clock()
			lastline=0 #hack to not send a lot of empty lines.... dont know where they come from... possibly a 'bug' in Report.c
			while (not self.kill_flag.isSet()) and self.prc.poll() is None: #short circuit when kill flag isSet -> prc=None
				
				try:
					line=self.prc.stdout.readline().rstrip()
				except:
					pass
				else:
					nchars=len(line)
					if nchars>0 or lastline>0:
						self.log_method(line)
						lastline=nchars
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


def GetOGRFormats(is_output=True):
	ogrlib.GetOGRDrivers(1,0)
	drivers=[]
	drv=ogrlib.GetOGRDrivers(0,1)
	while drv is not None:
		if drv in OGR_SHORT_TO_LONG:
			drivers.extend(OGR_SHORT_TO_LONG[drv])
		else:
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



	
	



if __name__=="__main__":
	f=GetOGRFormats()
	print repr(f)
	
	