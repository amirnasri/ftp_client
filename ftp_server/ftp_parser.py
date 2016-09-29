'''
Handle responses from the server to ftp raw commands.
'''

from enum import Enum


class connection_closed_error(Exception): pass
class request_error(Exception): pass

class request:
	def __init__(self):
		self.is_complete = False
		self.line = None
		self.type = 0

	def process_string(self, s):
		''' Parse a string received from the client into lines
		and then process each line. '''
		while True:
			# TODO: change '\r\n' to '\r*\n'
			rn_pos = s.find(b'\r\n')
			if (rn_pos == -1):
				break
			newline = s[:rn_pos + 2]
			s = s[rn_pos + 2:]
			self.line = newline
			self.type = newline.split()[0].strip()
			if len(self.type) < 3:
				request_error
			self.is_complete = True
		return s

	def print_request(self):
		print(self.line.decode('ascii'), end='')

class ftp_server_parser:
	def __init__(self):
		self.buff = bytearray()
		self.req = None

	def get_request(self, str):
		if not self.req:
			self.req = request()
		req = self.req
		self.buff = req.process_string(self.buff + str)
		if req.is_complete:
			req.print_request()
			self.req = None
			return req
		return None
