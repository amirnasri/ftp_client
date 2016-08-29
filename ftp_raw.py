'''
Handle responses from the server to ftp raw commands.
'''
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
    @staticmethod
    def get_resp(client_socket):
        resp = response()
        buff = bytearray()
        while True:
            s = client_socket.recv(ftp_raw_resp_handler.READ_BLOCK_SIZE)
            if (s == ''):
                return None
            buff = resp.process_string(buff + s)
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
        print("%s:%d\n" % (trans.server_address, trans.server_port))
        
    @staticmethod
    def handle_pwd(resp):
        first_line = resp.lines[0]
        last_sp = first_line.rfind(b' ')
        if (last_sp == -1):
            raise pwd_resp_error
        resp.cwd = first_line[last_sp+1:]
        
