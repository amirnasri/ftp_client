import socket
import os
import time
from ftp_raw import ftp_raw_resp_handler


# Type of data transfer on the data channel
class transfer_type:
    list = 1
    file = 2
    

class ftp_session:
	cmd_table = {}
	def __init__(self, server, port = 21):
		self.server = server
		self.port = port
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client.connect((server, port))
		self.load_text_file_extensions()
		self.cwd = ''
		if (len(ftp_session.cmd_table) == 0):
			ftp_session.cmd_table['get'] = self.get
			ftp_session.cmd_table['ls'] = self.ls
		
	def send_raw_command(self, command):
		print(command.strip())
		self.client.send(bytes(command, 'ascii'))

	def load_text_file_extensions(self):
		self.text_file_extensions = set()
		print(os.getcwd())
		f = open('text_file_extensions')
		for line in f:
			self.text_file_extensions.add(line.strip())
			
	def wait_welcome_msg(self):
		ftp_raw_resp_handler.get_resp(self.client)

	@staticmethod
	def calculate_data_rate(filesize, seconds):
		return filesize/seconds
	
	def get(self, path, verbose = 'True'):

		slash = path.rfind('/')
		if (slash != -1):
			filename = path[slash + 1:]
		else:
			filename = path
		file_ext = filename[filename.rfind('.'):]

		# Send TYPE depending on the type of the file 
		if (file_ext in self.text_file_extensions):
			self.trans.type = 'A'
			self.send_raw_command("TYPE A\r\n")
		else:
			self.trans.type = 'I'
			self.send_raw_command("TYPE I\r\n")
		resp = frrh.handle_generic(self.client)

		# Send PASV command to prepare for data transfer
		self.send_raw_command("PASV\r\n")
		resp = frrh.handle_pasv()

		
		if (verbose):
			print("Requesting file %s from the ftp server..." % filename)
		data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		data_socket.connect((self.resp.trans.server_address, self.resp.trans.server_port))
		self.send_raw_command("RETR %s\r\n" % path)
		ftp_raw_resp_handler.get_resp(self.client)
		f = open(filename, "wb")
		filesize = 0
		curr_time = time.time()
		while True:
			file_data = data_socket.recv(ftp_session.READ_BLOCK_SIZE)
			if (file_data == b''):
				break
			if (self.trans.type == 'A'):
				file_data = bytes(file_data.decode('ascii').replace('\r\n', '\n'), 'ascii')
			f.write(file_data)
			filesize += len(file_data)
		elapsed_time = time.time()- curr_time
		resp = self.get_resp()
		f.close()
		if (verbose):
			print("%d bytes received in %f seconds (%.2f b/s)."  
				%(filesize, elapsed_time, ftp_session.calculate_data_rate(filesize, elapsed_time)))
		
	def ls(self, filename=''):
		self.send_raw_command("PASV\r\n")
		resp = self.get_resp()
		self.handle_pasv_resp(resp)
		data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		data_socket.connect((self.trans.server_address, self.trans.server_port))
		self.send_raw_command("LIST %s\r\n" % filename)
		resp = self.get_resp()
		while True:
			ls_data = data_socket.recv(ftp_session.READ_BLOCK_SIZE).decode('ascii')
			if (ls_data == ''):
				break
			print(ls_data, end='')
		print()
		resp = self.get_resp()

	def pwd(self):		
		self.send_raw_command("PWD\r\n")
		resp = ftp_raw_resp_handler.get_resp(self.client)
		ftp_raw_resp_handler.handle_pwd(resp)
		self.cwd = resp.cwd

	def get_cwd(self):
		if (not self.cwd):
			self.pwd()
		return self.cwd
		
	def cd(self, path=''):
		if (not path):
			self.send_raw_command("PWD\r\n")
		else:
			self.send_raw_command("CWD %s\r\n" % path)
		resp = self.get_resp()
		
		

	def login(self, username, password = None):
		self.wait_welcome_msg()
		self.send_raw_command("USER %s\r\n" % username)
		resp = ftp_raw_resp_handler.get_resp(self.client)
		if (resp.resp_code == 331):
			if not (password):
				raise login_error
			self.send_raw_command("PASS %s\r\n" % password)
			resp = ftp_raw_resp_handler.get_resp(self.client)
			if (resp.resp_code != 230):
				raise login_error
		elif (resp.resp_code == 230):
			return
		else:
			raise login_error

	def run_command(self, cmd_line):
		''' run a single ftp command received from the ftp_cli module.
		'''
		cmd_line = cmd_line.split()
		cmd = cmd_line[0]
		cmd_args = cmd_line[1:]
		if (cmd in self.cmd_table):
			ftp_session.cmd_table[cmd](*cmd_args)
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