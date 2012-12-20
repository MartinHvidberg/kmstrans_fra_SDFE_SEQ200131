BUFFER_MAX=100
import sys
class PythonConsole(object):
	def __init__(self,locals):
		self.python_locals=locals
		self.cmd_buffer=[]
		self.index=-1
	def ClearCache(self):
		self.cmd_buffer=[]
		self.index=-1
	def ExecuteCode(self,code_lines):
		simple=False
		code=None
		lines=code_lines.splitlines()
		try:
			code=compile(code_lines,"<string>","single")
		except Exception,msg1:
			try:
				code=compile(code_lines,"<string>","exec")
			except Exception,msg2:
				sys.stderr.write(repr(msg2))
				sys.stderr.flush()
		else:
			simple=True
			self.AddToCommandBuffer(lines[-1])
		if code is not None:
			try:
				eval(code,{},self.python_locals)
			except Exception,msg:
				sys.stderr.write(repr(msg))
				sys.stderr.flush()
			else:
				return True
		
		return False
	def AddToCommandBuffer(self,cmd):
		if len(self.cmd_buffer)==BUFFER_MAX:
			self.cmd_buffer.pop(0)
		self.cmd_buffer.append(cmd)
	def SpoolUp(self):
		self.index+=1
		self.index=self.index%len(self.cmd_buffer)
		return self.cmd_buffer[self.index]
	def SpoolDown(self):
		self.index-=1
		self.index=self.index%len(self.cmd_buffer)
		return self.cmd_buffer[self.index]
	
				
		
		