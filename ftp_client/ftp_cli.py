import ftp_session
from ftp_session import connection_closed_error
import sys

class cli_error(BaseException): pass

class ftp_cli:
    def proc_input_args(self):
        ''' Parse command arguments and use them to start a ftp session. 
        '''
        if len(sys.argv) != 2:
            print('Usage: %s [username[:password]@]server[:port]' % sys.argv[0])
            raise cli_error

        username = ''
        password = ''
        server_path = ''
        port = 21
        
        arg1 = sys.argv[1]
        server = arg1
        at = arg1.find('@')
        if (at != -1):
            username = arg1[:at]
            server = arg1[at+1:]
        colon = username.find(':')
        if (colon != -1):
            password = username[colon+1:]
            username = username[:colon]
        # Pasrse server segment
        slash = server.find('/')
        if (slash != -1):
            server_path = server[slash + 1:]
            server = server[:slash]
        colon = server.find(':')
        if (colon != -1):
            port = int(server[colon+1:])
            server = server[:colon]
        ftp = ftp_session.ftp_session(server, port)
        if not username:
            username = input('Username:')
        if not password:
            password = input('Password:')
        ftp.login(username, password)
        if server_path:
            ftp.cd(server_path)
        self.ftp = ftp
        self.username = username
        self.password = password
        self.server = server
        self.port = port
        self.proc_cli()
    
    def print_prompt(self):
        print('%s@%s: %s> ' % (self.username, self.server, self.ftp.get_cwd()), end = '')
    def proc_cli(self):
        ''' Process user input and translate them to appropriate ftp commands.
        '''
        while True:
            self.print_prompt()
            try:
                cmd_line = input()
                if not cmd_line.strip():
                    continue
                self.ftp.run_command(cmd_line)
            except ftp_session.cmd_not_implemented_error:
                print("command not implemented")
            except connection_closed_error:
                print("connection was closed by the server.")
                break
            except ftp_session.quit_error:
                print("Goodbye.")
                break
            except (EOFError, KeyboardInterrupt):
                print("")
                break
            #except BaseException:
            #    print("")
            #    break


if (__name__ == '__main__'):
    cli = ftp_cli()
    try:
        cli.proc_input_args()
    except (cli_error):
        pass
    
