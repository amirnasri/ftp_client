import socket


class response:
	def __init__(self):
		self.is_complete = False
		self.lines = []
		self.multiline = False
		self.resp_code = 0

	def process_string(self, s):
		while True:
			rn_pos = s.find('\r\n')
			if (rn_pos == -1):
				break
			self.lines.append(s[:rn_pos + 2])
			s = s[rn_pos + 2:]
		
		if (self.resp_code == 0 and len(self.lines) > 0):
			resp_code = int(self.lines[0][:3])
			if (resp_code > 100 and resp_code < 600):
				self.resp_code = resp_code
			if (self.lines[0][3] == '-'):
				self.multiline = True

		if (self.multiline):
			if (int(self.lines[-1][:3]) == self.resp_code and self.lines[-1][3] == ' '):
				self.is_complete = True
		else:
			if (len(self.lines) != 0):
				self.is_complete == True
 		return s

	def print_resp(self):
		for l in self.lines:
			print(l)

class ftp_session:
	READ_BLOCK_SIZE = 4048
	def __init__(self, server, port):
		self.server = server
		self.port = port
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client.connect((server, port))
		self.buff = ''

	def wait_welcome_msg(self):
		self.get_resp()
	
	def get_resp(self):
		self.resp = response()
		while True:
			s = self.client.recv(ftp_session.READ_BLOCK_SIZE)
			if (s == ''):
				break
			self.buff = self.resp.process_string(self.buff + s)
			if (self.resp.is_complete):
				break
			
		self.resp.print_resp()
		#self.client.close()

	def send_command(self, command):
		self.client.send(command)	

	def get(self, filename):
		self.send_command("PASV\r\n")
		self.get_resp()

	def login(self, username, password = None):
		self.send_command("USER %s\r\n" % username)
		self.get_resp()
		print("here!!!")
		print(self.resp.resp_code)
		if (self.resp.resp_code == 331):
			if not (password):
				raise login_error
			self.send_command("PASS %s\r\n" % password)
			self.get_resp()
			if (self.resp.resp_code != 230):
				raise login_error
		elif (self.resp.resp_code == 230):
			return
		else:
			raise login_error

	def session_close(self):
		self.client.close()
			
if (__name__ == '__main__'):
	ftp = ftp_session("localhost", 21)
	ftp.wait_welcome_msg()
	try:
		ftp.login("amir", "salam")
	except:
		print("login failed.")

	ftp.session_close()
