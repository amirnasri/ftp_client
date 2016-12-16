import sys
import socket
from ftp_parser import ftp_server_parser

class ftp_raw_cmd_handler:
    @staticmethod
    def user(req):
        
        

class client:
    def __init__(self, socket):
        self.socket = socket[0]
        self.client_addr = socket[1]
        self.send_welcome_msg()
        self.parser = ftp_server_parser()
        print("received coonnection from (%s, %s)" % self.client_addr)
        self.proc_client()

    def send_welcome_msg(self):
        self.socket.send(b"220 welcome to amir ftp server\r\n")

    def get_request(self):
        while True:
            s = self.socket.recv(ftp_session.READ_BLOCK_SIZE)
            if (s == b''):
                raise connection_closed_error
            req = self.parser.get_request(s)
            if req:
                break
        #resp_handler = ftp_raw.get_resp_handler(self.cmd)
        #if resp_handler:
        #    resp_handler(resp)
        return req

    def proc_client(self):
        req = self.get_request()

class ftp_server:
    FTP_SERVER_PORT = 8001
    READ_BLOCK_SIZE = 1024
    
    def __init__(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = ftp_server.FTP_SERVER_PORT
        if len(sys.argv) > 1:
            port = int(sys.argv[1])
        server.bind(("localhost", port))
        server.listen(5)
        self.server = server
        print('ftp server listening on port %d' % ftp_server.FTP_SERVER_PORT)
        while True:
            client_socket = server.accept()
            client(client_socket)


        
if __name__ == '__main__':
    session = ftp_server()
        