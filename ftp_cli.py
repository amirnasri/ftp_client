import ftp_session
import sys

class cli_error(BaseException): pass

class ftp_cli:
    def proc_args(self):
        if len(sys.argv) != 2:
            print('Usage: %s server' % sys.argv[0])
            raise cli_error
        arg1 = sys.argv[1]
        at = arg1.find('@')
        username = ''
        server = arg1
        if (at != -1):
            username = arg1[:at]
            server = arg1[at+1:]
        colon = server.find(':')
        port = 21
        if (colon != -1):
            port = int(server[colon+1:])
            server = server[colon]  
        ftp = ftp_session.ftp_session(server, port)
        if (username == ''):
            username = input('Username:')
        password = input("Password:")
        ftp.login(username, password)
        self.ftp = ftp
        self.proc_input()
    
    def proc_input(self):
        
        while True:
            print('> ', end = '')
            cmd = input()
            cmd = cmd.split()
            if (cmd[0] == 'get'):
                #ftp.ls("upload")
                self.ftp.get(cmd[1])
            elif (cmd[0] == 'ls'):
                if (len(cmd) == 1):
                    self.ftp.ls("")
                else:
                    self.ftp.ls(cmd[1])
            else:
                raise cli_error
            
        

if (__name__ == '__main__'):
    cli = ftp_cli()
    try:
        cli.proc_args()
    except (cli_error):
        pass
    
