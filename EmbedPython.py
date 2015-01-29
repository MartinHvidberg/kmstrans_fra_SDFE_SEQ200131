BUFFER_MAX=100
import sys
class PythonConsole(object):
	def __init__(self,namespace):
		self.namespace=namespace
		self.cmd_buffer=[]
		self.index=-1
	def clearCache(self):
		self.cmd_buffer=[]
		self.index=-1
	def executeCode(self,code_lines):
		#TODO weird namespace stuff in class definitions....
		simple=False
		code=None
		err=None
		lines=code_lines.splitlines()
		if len(lines)<2:
			try:
				code=compile(code_lines,"<string>","single")
			except Exception,msg1:
				err=msg1
			else:
				simple=True
		if code is None:
			try:
				code=compile(code_lines,"<string>","exec")
			except Exception,msg2:
				err=msg2
		if code is not None:
			try:
				eval(code,self.namespace)
			except Exception,msg:
				sys.stderr.write(repr(msg))
				sys.stderr.flush()
			else:
				if simple:
					self.addToCommandBuffer(lines[-1])
				return True
		else:
			sys.stderr.write(repr(err))
			sys.stderr.flush()
		return False
	def updateNameSpace(self,key,value):
		self.namespace[key]=value
	def addToCommandBuffer(self,cmd):
		if len(self.cmd_buffer)==BUFFER_MAX:
			self.cmd_buffer.pop(0)
		self.cmd_buffer.append(cmd)
	def spoolUp(self):
		self.index+=1
		self.index=self.index%len(self.cmd_buffer)
		return self.cmd_buffer[self.index]
	def spoolDown(self):
		self.index-=1
		self.index=self.index%len(self.cmd_buffer)
		return self.cmd_buffer[self.index]
	
				
		
		