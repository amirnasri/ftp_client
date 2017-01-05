import socket
import os
import time
from ftp_raw import ftp_raw_resp_handler as ftp_raw
from ftp_parser import response_error
from ftp_parser import ftp_client_parser
import inspect
import subprocess

class ftp_error(Exception): pass
class cmd_not_implemented_error(ftp_error): pass
class quit_error(ftp_error): pass
class connection_closed_error(ftp_error): pass

'''
TODO:
- Fixe get argument parsing
- Add mkdir, rm, rmdir, mv, status, user, pass, site, active(port), lcd, chmod, cat, help, put (use lftp syntax)
- Add command completion using tab based on method documents
- Add history search using arrow key
- Add installation using python setup.py
- Add !command for executing shell commands
'''
def ftp_command(f):
	f.ftp_command = True
	return f


def check_args(f):
	def new_f(*args, **kwargs):
		if hasattr(f, '__doc__'):
			doc = f.__doc__.split('\n')
			doc_ = None
			for line in doc:
				p = line.find('usage:')
				if p != -1:
					doc_ = line[p + 6:]
					break
			if doc_:
				n_args = len(doc_.split()) - 1
				print(n_args, args, kwargs)
				assert n_args == len(args[1]), \
					"%s expects %d arguments, %d given.\nusage: %s" % (new_f.__code__.co_name, n_args, len(args[1]), doc_)
				f(*args, **kwargs)

	return new_f

# Type of data transfer on the data channel
class transfer_type:
	list = 1
	file = 2

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

class ftp_session:
	READ_BLOCK_SIZE = 1024

	def __init__(self, server, port=21):
		self.text_file_extensions = set()
		self.server = server
		self.port = port
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client.connect((server, port))
		self.load_text_file_extensions()
		self.cwd = ''
		self.cmd = None
		self.transfer_type = None
		self.parser = ftp_client_parser()
		self.passive = False
		self.verbose = True

	def send_raw_command(self, command):
		if self.verbose:
			print(command.strip())
		self.client.send(bytes(command, 'ascii'))
		self.cmd = command.split()[0].strip()

	def get_resp(self):
		while True:
			s = self.client.recv(ftp_session.READ_BLOCK_SIZE)
			#print("string received from server: %s" % s)
			if (s == b''):
				raise connection_closed_error
			resp = self.parser.get_resp(s, self.verbose)
			#print(resp)
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

	@classmethod
	def print_usage(cls):
		fname = inspect.stack()[1][3]
		if hasattr(cls, fname):
			doc = getattr(getattr(cls, fname), '__doc__', None)
			if doc:
				doc = doc.split('\n')
				for line in doc:
					p = line.find('usage:')
					if p != -1:
						print(line[p:])
	@ftp_command
	def ascii(self, args):
		if len(args) != 0:
			ftp_session.print_usage()
			return
		self.transfer_type = 'A'
		print("Switched to ascii mode")

	@ftp_command
	def binary(self, args):
		if len(args) != 0:
			ftp_session.print_usage()
			return
		self.transfer_type = 'I'
		print("Switched to binary mode")

	@staticmethod
	def get_file_info(path):
		# Get filename and file extension from path
		slash = path.rfind('/')
		if slash != -1:
			filename = path[slash + 1:]
		else:
			filename = path
		dot = filename.rfind('.')
		file_ext = ''
		if dot != -1:
			file_ext = filename[filename.rfind('.'):]
		return filename, file_ext

	def setup_data_transfer(self, data_command):
		# Send PASV or Port command to prepare for data transfer
		if self.passive:
			self.send_raw_command("PASV\r\n")
			resp = self.get_resp()
			data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			data_socket.connect((resp.trans.server_address, resp.trans.server_port))
			self.send_raw_command(data_command)
			self.get_resp()
		else:
			s = socket.socket()
			s.connect(("8.8.8.8", 80))
			ip = s.getsockname()[0]
			s.close()
			if not ip:
				raise ftp_error("Could not get local IP address.")
			data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			data_socket.bind((ip, 0))
			data_socket.listen(1)
			_, port = data_socket.getsockname()
			if not port:
				raise ftp_error("Could not get local port.")

			port_h = int(port/256)
			port_l = port - port_h * 256
			self.send_raw_command("PORT %s\r\n" % (",".join(ip.split('.') + [str(port_h), str(port_l)])))
			resp = self.get_resp()
			self.send_raw_command(data_command)
			resp = self.get_resp()
			data_socket, address = data_socket.accept()
			#print("connection received from client %s" % str(address))
			if address[0] != self.client.getpeername()[0]:
				data_socket.close()
				data_socket = None
		return data_socket

	@ftp_command
	def get(self, args):
		'''	usage: get path-to-file '''
		if len(args) != 1:
			ftp_session.print_usage()
			return
		path = args[0]
		filename, file_ext = ftp_session.get_file_info(path)
		# If transfer type is not set, send TYPE command depending on the type of the file
		# (TYPE A for ascii files and TYPE I for binary files)
		transfer_type = self.transfer_type
		if transfer_type is None:
			if file_ext != '' and file_ext in self.text_file_extensions:
				transfer_type = 'A'
			else:
				transfer_type = 'I'
		self.send_raw_command("TYPE %s\r\n" % transfer_type)
		self.get_resp()

		if self.verbose:
			print("Requesting file %s from the ftp server...\n" % filename)

		data_socket = self.setup_data_transfer("RETR %s\r\n" % path)

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
		data_socket.close()
		if self.verbose:
			print("%d bytes received in %f seconds (%.2f b/s)."
				%(filesize, elapsed_time, ftp_session.calculate_data_rate(filesize, elapsed_time)))

	@ftp_command
	def put(self, args):
		'''	usage: get path-to-file '''
		if len(args) != 1:
			ftp_session.print_usage()
			return
		path = args[0]
		filename, file_ext = ftp_session.get_file_info(path)
		# If transfer type is not set, send TYPE command depending on the type of the file
		# (TYPE A for ascii files and TYPE I for binary files)
		transfer_type = self.transfer_type
		if transfer_type is None:
			if file_ext != '' and file_ext in self.text_file_extensions:
				transfer_type = 'A'
			else:
				transfer_type = 'I'
		self.send_raw_command("TYPE %s\r\n" % transfer_type)
		self.get_resp()

		if self.verbose:
			print("Sending file %s to the ftp server...\n" % filename)

		data_socket = self.setup_data_transfer("STOR %s\r\n" % path)

		f = open(filename, "rb")
		filesize = 0
		curr_time = time.time()
		while True:
			file_data = f.read(ftp_session.READ_BLOCK_SIZE)
			if file_data == b'':
				break
			if self.transfer_type == 'A':
				file_data = bytes(file_data.decode('ascii').replace('\r\n', '\n'), 'ascii')
			data_socket.send(file_data)
			filesize += len(file_data)
		elapsed_time = time.time()- curr_time
		data_socket.close()
		f.close()
		self.get_resp()
		if self.verbose:
			print("%d bytes sent in %f seconds (%.2f b/s)."
				%(filesize, elapsed_time, ftp_session.calculate_data_rate(filesize, elapsed_time)))

	def get_colored_ls_data(ls_data):
		lines = ls_data.split('\r\n')
		colored_lines = []
		import re
		for l in lines:
			#re.sub(r'(d.*\s+(\w+\s+){7})(\w+)')
			if l and l[0] == 'd':
				p = l.rfind(' ')
				if p != -1:
					l = l[:p + 1] + bcolors.BOLD + bcolors.OKBLUE + l[p + 1:] + bcolors.ENDC
			colored_lines.append(l)

		return "\r\n".join(colored_lines)

	'''	usage: ls [dirname] '''
	@ftp_command
	def ls(self, args):

		if len(args) > 1:
			ftp_session.print_usage()
			return
		filename = ''
		if len(args) == 1:
			filename = args[0]

		'''
		self.send_raw_command("PASV\r\n")
		resp = self.get_resp()
		data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		data_socket.connect((resp.trans.server_address, resp.trans.server_port))
		'''
		data_command = "LIST %s\r\n" % filename
		data_socket = self.setup_data_transfer(data_command)
		if not data_socket:
			return

		ls_data = ''
		while True:
			ls_data_ = data_socket.recv(ftp_session.READ_BLOCK_SIZE).decode('ascii')
			if ls_data_ == '':
				break
			ls_data += ls_data_
		ls_data_colored = ftp_session.get_colored_ls_data(ls_data)
		print(ls_data_colored, end='')
		data_socket.close()
		if self.verbose:
			print()
		self.get_resp()

	@ftp_command
	def pwd(self, args=None):
		self.send_raw_command("PWD\r\n")
		resp = self.get_resp()
		self.cwd = resp.cwd

	def get_cwd(self):
		if not self.cwd:
			self.pwd()
		return self.cwd

	@ftp_command
	def cd(self, args):
		'''
			usage: cd [dirname]
		'''
		if len(args) > 1:
			ftp_session.print_usage()
			return
		path = None
		if len(args) == 1:
			path = args[0]

		if not path:
			self.send_raw_command("PWD\r\n")
			self.get_resp()
		else:
			self.send_raw_command("CWD %s\r\n" % path)
			self.get_resp()
			self.send_raw_command("PWD\r\n")
			resp = self.get_resp()
			self.cwd = resp.cwd

	@ftp_command
	def passive(self, args):
		'''
			usage: passive [on|off]
		'''
		if len(args) > 1:
			ftp_session.print_usage()
			return
		if len(args) == 0:
			self.passive = not self.passive
		elif len(args) == 1:
			if args[0] == 'on':
				self.passive = True
			elif args[0] == 'off':
				self.passive = False
			else:
				ftp_session.print_usage()
				return
		print("passive %s" % ('on' if self.passive else 'off'))

	@ftp_command
	def verbose(self, args):
		'''
			usage: verbose [on|off]
		'''
		if len(args) > 1:
			ftp_session.print_usage()
			return
		if len(args) == 0:
			self.verbose = not self.verbose
		elif len(args) == 1:
			if args[0] == 'on':
				self.verbose = True
			elif args[0] == 'off':
				self.verbose = False
			else:
				ftp_session.print_usage()
				return
		print("verbose %s" % ('on' if self.verbose else 'off'))

	@ftp_command
	def mkdir(self, dirname):
		self.send_raw_command("MKD %s\r\n" % dirname)
		self.get_resp()

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

	@ftp_command
	def quit(self):
		raise quit_error
	def run_command(self, cmd_line):
		''' run a single ftp command received from the ftp_cli module.
		'''
		if cmd_line[0] == '!':
			subprocess.run(cmd_line[1:], shell=True)
			return
		cmd_line = cmd_line.split()
		cmd = cmd_line[0]
		cmd_args = cmd_line[1:]
		if hasattr(ftp_session, cmd):
			try:
				getattr(ftp_session, cmd)(self, cmd_args)
			except response_error:
				pass
		else:
			raise cmd_not_implemented_error

	def session_close(self):
		self.client.close()

if __name__ == '__main__':
	ftp = ftp_session("172.18.2.169", 21)
	#try:
	ftp.login("anonymous", "p")
	ftp.ls("upload")
	ftp.get("upload/anasri/a.txt")
	#except:
	#print("login failed.")

	ftp.session_close()