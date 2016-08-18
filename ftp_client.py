import socket


class response:
	def __init__(self):
		self.is_complete = False
		self.lines = []
		self.multiline = False
		self.resp_code = 0

	def process_string(self, s):
		while True:
			rn_pos = s.find(b'\r\n')
			if (rn_pos == -1):
				break
			self.lines.append(s[:rn_pos + 2])
			s = s[rn_pos + 2:]

		if (self.resp_code == 0 and len(self.lines) > 0):
			resp_code = int(self.lines[0][:3])
			if (resp_code > 100 and resp_code < 600):
				self.resp_code = resp_code
			if (chr(self.lines[0][3]) == '-'):
				self.multiline = True

		if (self.multiline):
			if (int(self.lines[-1][:3]) == self.resp_code and chr(self.lines[-1][3]) == ' '):
				self.is_complete = True
		else:
			if (len(self.lines) != 0):
				self.is_complete = True
		return s

	def print_resp(self):
		for l in self.lines:
			print(l.decode('ascii'), end = '')
		print("")

class ftp_session:
	def __init__(self, server, port):
		self.server = server
		self.port = port
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client.connect((server, port))
		self.buff = bytearray()

	def wait_welcome_msg(self):
		self.resp = self.get_resp()

	READ_BLOCK_SIZE = 2048
	def get_resp(self):
		resp = response()
		while True:
			s = self.client.recv(ftp_session.READ_BLOCK_SIZE)
			if (s == ''):
				break
			self.buff = resp.process_string(self.buff + s)
			if (resp.is_complete):
				break

		resp.print_resp()
		return resp
		#self.client.close()

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
		transfer = 1
		transfer.ip = ip = '.'.join(ip_port_array[0:4])
		transfer.port = (int(ip_port_array[4]) << 8) + int(ip_port_array[5])
		print("%s:%d\n" % (ip, port))
		data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		data_socket.connect((ip, port))


	def get(self, filename):
		self.send_command("PASV\r\n")
		resp = self.get_resp()
		self.parse_pasv_resp(resp)

	def login(self, username, password = None):
		self.send_command("USER %s\r\n" % username)
		self.resp = self.get_resp()
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
	#try:
	ftp.login("anonymous", "")
	ftp.get("fdfd")
	#except:
	#print("login failed.")

	ftp.session_close()
