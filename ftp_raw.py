'''
Handle responses from the server to ftp raw commands.
'''

from enum import Enum

class connection_closed_error(Exception): pass
class transfer(object):
    pass

class response:
    def __init__(self):
        self.is_complete = False
        self.lines = []
        self.multiline = False
        self.resp_code = 0
        
    def process_newline(self, newline):
        if not self.multiline:
            # Only the first line of response comes here (for both single-line and multiline responses).
            resp_code = int(newline[:3])
            if (resp_code > 100 and resp_code < 600 and
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
        ''' Parse a string received from the server into lines
        and then process each line. ''' 
        while True:
            # TODO: change '\r\n' to '\r*\n'
            rn_pos = s.find(b'\r\n')
            if (rn_pos == -1):
                break
            newline = s[:rn_pos + 2]
            s = s[rn_pos + 2:]
            self.process_newline(newline)
            self.lines.append(newline)
        return s

    def print_resp(self):
        for l in self.lines:
            print(l.decode('ascii'), end = '')
        print("")
        


class ftp_raw_resp_handler:
    READ_BLOCK_SIZE = 10
    resp_handler_table = {}

    class ftp_res_type(Enum):
        interm = 1
        successful = 2
        more_needed = 3
        fail = 4
        error = 5
    
    @staticmethod
    def init():
        if not ftp_raw_resp_handler.resp_handler_table:
                ftp_raw_resp_handler.resp_handler_table['PASV'] = ftp_raw_resp_handler.handle_pasv
                ftp_raw_resp_handler.resp_handler_table['PWD'] = ftp_raw_resp_handler.handle_pwd

    @staticmethod
    def get_resp_(client_socket):
        resp = response()
        buff = bytearray()
        while True:
            s = client_socket.recv(ftp_raw_resp_handler.READ_BLOCK_SIZE)
            if (s == b''):
                raise connection_closed_error
            buff = resp.process_string(buff + s)
            if resp.is_complete:
                resp.res_type = ftp_raw_resp_handler.ftp_res_type(int(resp.resp_code/100))
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
    @staticmethod
    def get_resp(client_socket, ftp_cmd = None):
        resp = ftp_raw_resp_handler.get_resp_(client_socket)
        if ftp_cmd and (ftp_cmd in ftp_raw_resp_handler.resp_handler_table):
            resp_handler = ftp_raw_resp_handler.resp_handler_table[ftp_cmd]
            resp_handler(resp)
        return resp

    @staticmethod
    def handle_pasv(resp):
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
        if (len(ip_port_array) != 6):
            raise pasv_resp_error
        trans = transfer()
        trans.server_address = '.'.join(ip_port_array[0:4])
        trans.server_port = (int(ip_port_array[4]) << 8) + int(ip_port_array[5])
        resp.trans = trans

    @staticmethod
    def handle_pwd(resp):
        first_line = resp.lines[0]
        quote = first_line.find(b'"')
        if (quote == -1):
            raise pwd_resp_error
        first_line = first_line[quote + 1:]
        quote = first_line.find(b'"')
        if (quote == -1):
            raise pwd_resp_error
        resp.cwd = first_line[:quote].decode('ascii')
        
ftp_raw_resp_handler.init()