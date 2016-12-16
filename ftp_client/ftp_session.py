import socket
import os
import time
from ftp_raw import ftp_raw_resp_handler as ftp_raw
from ftp_parser import response_error
from ftp_parser import ftp_client_parser

class cmd_not_implemented_error(Exception): pass
class quit_error(Exception): pass
class connection_closed_error(Exception): pass
import os

# Type of data transfer on the data channel
class transfer_type:
	list = 1
	file = 2

class ftp_session:
	READ_BLOCK_SIZE = 10

	def __init__(self, server, port=21):
		self.text_file_extensions = set()
		self.server = server
		self.port = port
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client.connect((server, port))
		self.load_text_file_extensions()
		self.cwd = ''
		self.cmd = None
		self.verbose = True
		self.transfer_type = None
		self.parser = ftp_client_parser()
		
	def send_raw_command(self, command):
		print(command.strip())
		self.client.send(bytes(command, 'ascii'))
		self.cmd = command.split()[0].strip()
		
	def get_resp(self):
		while True:
			s = self.client.recv(ftp_session.READ_BLOCK_SIZE)
			if (s == b''):
				raise connection_closed_error
			resp = self.parser.get_resp(s)
			if resp:
				break
		resp_handler = ftp_raw.get_resp_handler(self.cmd)
		if resp_handler:
			resp_handler(resp)
		return resp

	def load_text_file_extensions(self):
		try:
			f = open('text_file_extensions')
			for line in f:
				self.text_file_extensions.add(line.strip())
		except:
			pass

	def get_welcome_msg(self):
		return self.get_resp()

	@staticmethod
	def calculate_data_rate(filesize, seconds):
		return filesize/seconds

	def ascii(self):
		self.transfer_type = 'A'
		print("Switched to ascii mode")

	def binary(self):
		self.transfer_type = 'I'
		print("Switched to binary mode")

	def get(self, *args):
		print(args)
		if len(args) == 0:
			print("usage: get path-to-file")
			return
		path = args[0]
		# Get filename and file extension from path
		slash = path.rfind('/')
		if slash != -1:
			filename = path[slash + 1:]
		else:
			filename = path
		file_ext = filename[filename.rfind('.'):]

		# If transfer type is not set, send TYPE command depending on the type of the file
		# (TYPE A for ascii files and TYPE I for binary files)
		transfer_type = self.transfer_type
		if transfer_type is None:
			if file_ext in self.text_file_extensions:
				transfer_type = 'A'
			else:
				transfer_type = 'I'
		self.send_raw_command("TYPE %s\r\n" % transfer_type)
		self.get_resp()

		# Send PASV command to prepare for data transfer
		self.send_raw_command("PASV\r\n")
		resp = self.get_resp()

		if (self.verbose):
			print("Requesting file %s from the ftp server...\n" % filename)
		data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		data_socket.connect((resp.trans.server_address, resp.trans.server_port))
		self.send_raw_command("RETR %s\r\n" % path)
		self.get_resp()
		f = open(filename, "wb")
		filesize = 0
		curr_time = time.time()
		while True:
			file_data = data_socket.recv(ftp_session.READ_BLOCK_SIZE)
			if file_data == b'':
				break
			if self.transfer_type == 'A':
				file_data = bytes(file_data.decode('ascii').replace('\r\n', '\n'), 'ascii')
			f.write(file_data)
			filesize += len(file_data)
		elapsed_time = time.time()- curr_time
		self.get_resp()
		f.close()
		if (self.verbose):
			print("%d bytes received in %f seconds (%.2f b/s)."  
				%(filesize, elapsed_time, ftp_session.calculate_data_rate(filesize, elapsed_time)))
		
	def ls(self, filename=''):
		self.send_raw_command("PASV\r\n")
		resp = self.get_resp()
		data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		data_socket.connect((resp.trans.server_address, resp.trans.server_port))
		self.send_raw_command("LIST %s\r\n" % filename)
		self.get_resp()
		while True:
			ls_data = data_socket.recv(ftp_session.READ_BLOCK_SIZE).decode('ascii')
			if (ls_data == ''):
				break
			print(ls_data, end='')
		print()
		self.get_resp()

	def pwd(self):		
		self.send_raw_command("PWD\r\n")
		resp = self.get_resp()
		self.cwd = resp.cwd

	def get_cwd(self):
		if not self.cwd:
			self.pwd()
		return self.cwd
		
	def cd(self, path=None):
		if not path:
			self.send_raw_command("PWD\r\n")
			self.get_resp()
		else:
			self.send_raw_command("CWD %s\r\n" % path)
			self.get_resp()
			self.send_raw_command("PWD\r\n")
			resp = self.get_resp()
			self.cwd = resp.cwd

	
	def login(self, username, password = None):
		self.get_welcome_msg()
		self.send_raw_command("USER %s\r\n" % username)
		resp = self.get_resp()
		if (resp.resp_code == 331):
			if not (password):
				raise login_error
			self.send_raw_command("PASS %s\r\n" % password)
			resp = self.get_resp()
			if (resp.resp_code != 230):
				raise login_error
		elif (resp.resp_code == 230):
			return
		else:
			raise login_error

	def quit(self):
		raise quit_error
	def run_command(self, cmd_line):
		''' run a single ftp command received from the ftp_cli module.
		'''
		cmd_line = cmd_line.split()
		cmd = cmd_line[0]
		cmd_args = cmd_line[1:]
		if hasattr(ftp_session, cmd):
			try:
				getattr(ftp_session, cmd)(self, *cmd_args)
			except response_error:
				pass
		else:
			raise cmd_not_implemented_error
		
	def session_close(self):
		self.client.close()

if (__name__ == '__main__'):
	ftp = ftp_session("172.18.2.169", 21)
	#try:
	ftp.login("anonymous", "p")
	ftp.ls("upload")
	ftp.get("upload/anasri/a.txt")
	#except:
	#print("login failed.")

	ftp.session_close()