import socket

class client:
    def __init__(self, client_socket):
        self.socket = client_socket
        self.send_welcome_msg()
        self.proc_client()
    
    def send_welcome_msg(self):
        self.socket.send("220 welcome to amir ftp server/r/n")
    
    def proc_client(self):
        
    
            

class ftp_session:
    FTP_SERVER_PORT = 8001
    READ_BLOCK_SIZE = 1024
    
    def __init__(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("localhost", ftp_session.FTP_SERVER_PORT))
        server.listen(5)
        self.server = server
        client_socket = server.accept()
        self.serv_client(client_socket)
        
        
    def serv_client(self, client_socket):
        client_socket.send
        s = client_socket.recv(ftp_session.READ_BLOCK_SIZE)
        if (s == ''):
            raise connection_closed_error
        
        
        
        