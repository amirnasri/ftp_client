import socket


class response:
	def __init__(self):
		self.is_complete = False
		self.lines = []
		self.multiline = False
		self.resp_code = 0
		
	def proc_newline(self, newline):
		if not self.multiline:
			# Only the first line of response comes here (for both single-line and multiline responses).
			resp_code = int(newline[:3])
			if (resp_code > 100 and resp_code < 600 and \
					(chr(newline[3]) == ' ' or chr(newline[3]) == '-')):
				self.resp_code = resp_code
			else:
				raise resp_parse_error
			
			if (chr(newline[3]) == '-'):
				self.multiline = True
			else:
				self.is_complete = True
		else:
			if (int(newline[:3]) == self.resp_code and chr(newline[3]) == ' '):
				self.is_complete = True
		
	def process_string(self, s):
		while True:
			# TODO: change '\r\n' to '\r*\n'
			rn_pos = s.find(b'\r\n')
			if (rn_pos == -1):
				break
			newline = s[:rn_pos + 2]
			s = s[rn_pos + 2:]
			self.proc_newline(newline)
			self.lines.append(newline)
		return s

	def print_resp(self):
		for l in self.lines:
			print(l.decode('ascii'), end = '')
		print("")
		
# Type of data transfer on the data channel
class transfer_type:
	list = 1
	file = 2
	
class transfer(object):
	pass

class ftp_session:
	def __init__(self, server, port):
		self.server = server
		self.port = port
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client.connect((server, port))
		self.buff = bytearray()
		
	def wait_welcome_msg(self):
		self.get_resp()

	READ_BLOCK_SIZE = 10
	def get_resp(self):
		resp = response()
		while True:
			s = self.client.recv(ftp_session.READ_BLOCK_SIZE)
			if (s == ''):
				return None
			self.buff = resp.process_string(self.buff + s)
			if (resp.is_complete):
				resp.print_resp()
				return resp
		#self.client.close()
	"""		
	def get_resp(self):
		if (len(self.resp_queue) == 0):
			while True:
				resp = self.get_resp_()
				''' If response is not complete we stop processing the responses untile the 
				next time get_resp is called. '''
				if resp is None:
					break
				''' Insert the new response at the begining of the (empty) queue. '''
				self.resp_queue.insert(0, resp)
				
		''' Pop the last response in the queue and return it. '''
		return self.resp_queue.pop()
	"""
	
	def send_command(self, command):
		self.client.send(bytes(command, 'ascii'))

	def parse_pasv_resp(self, resp):
		if (len(resp.lines) != 1):
			raise pasv_resp_error
		resp_line = resp.lines[0].decode('ascii')
		lpos = resp_line.find('(')
		if (lpos == -1):
			raise pasv_resp_error
		resp_line = resp_line[lpos + 1:]
		rpos = resp_line.find(')')
		if (rpos == -1):
			raise pasv_resp_error
		resp_line = resp_line[:rpos]
		ip_port_array = resp_line.split(',')
		print(ip_port_array)
		if (len(ip_port_array) != 6):
			raise pasv_resp_error
		trans = transfer()
		trans.server_address = '.'.join(ip_port_array[0:4])
		trans.server_port = (int(ip_port_array[4]) << 8) + int(ip_port_array[5])
		self.trans = trans
		print("%s:%d\n" % (trans.server_address, trans.server_port))
		

	def get(self, filename):
		self.send_command("PASV\r\n")
		resp = self.get_resp()
		self.parse_pasv_resp(resp)
		data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		data_socket.connect((self.d.ip, self.d.port))
		self.send_command("RETR %s\r\n" % filename)
		print(data_socket.recv(ftp_session.READ_BLOCK_SIZE).decode('ascii'))
		
	def ls(self, filename):
		self.send_command("PASV\r\n")
		resp = self.get_resp()
		self.parse_pasv_resp(resp)
		data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		data_socket.connect((self.trans.server_address, self.trans.server_port))
		self.send_command("LIST %s\r\n" % filename)
		while True:
			ls_data = data_socket.recv(ftp_session.READ_BLOCK_SIZE).decode('ascii')
			if (ls_data == ''):
				break
			print(ls_data, end='')
		print()

	def login(self, username, password = None):
		self.send_command("USER %s\r\n" % username)
		resp = self.get_resp()
		if (resp.resp_code == 331):
			if not (password):
				raise login_error
			self.send_command("PASS %s\r\n" % password)
			resp = self.get_resp()
			if (resp.resp_code != 230):
				raise login_error
		elif (resp.resp_code == 230):
			return
		else:
			raise login_error

	def session_close(self):
		self.client.close()

if (__name__ == '__main__'):
	ftp = ftp_session("localhost", 21)
	ftp.wait_welcome_msg()
	#try:
	ftp.login("anonymous", "")
	ftp.ls("/Temp/fortidev4-fsoc1/bin/openssl")
	#except:
	#print("login failed.")

	ftp.session_close()
