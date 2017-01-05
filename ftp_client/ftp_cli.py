import ftp_session
from ftp_session import connection_closed_error
import sys
import getpass

class cli_error(BaseException): pass


import readline
import types


def get_ftp_commands():
    l = []
    for k, v in ftp_session.ftp_session.__dict__.items() :
        if type(v) == types.FunctionType and hasattr(v, 'ftp_command'):
            l.append(k)
    return l

class Completer(object):
    def __init__(self, options):
        self.options = sorted(options)
        return

    def complete(self, text, state):
        response = None
        if state == 0:
            # This is the first time for this text, so build a match list.
            if text:
                self.matches = [s
                                for s in self.options
                                if s and s.startswith(text)]
            else:
                self.matches = self.options[:]

        # Return the state'th item from the match list,
        # if we have that many.
        try:
            response = self.matches[state]
        except IndexError:
            response = None
        return response

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
        user_colon = username.find(':')
        if (user_colon != -1):
            password = username[user_colon+1:]
            username = username[:user_colon]
        # Pasrse server segment
        slash = server.find('/')
        if (slash != -1):
            server_path = server[slash + 1:]
            server = server[:slash]
        server_colon = server.find(':')
        if (server_colon != -1):
            port = int(server[server_colon+1:])
            server = server[:server_colon]
        ftp = ftp_session.ftp_session(server, port)
        if not username:
            username = input('Username:')
        if not password and user_colon == -1:
            password = getpass.getpass(prompt='Password:')
        if not password and username == 'anonymous':
            password = 'password'
        ftp.login(username, password)
        if server_path:
            ftp.cd([server_path])
        self.ftp = ftp
        self.username = username
        self.password = password
        self.server = server
        self.port = port
        self.proc_cli()
    
    def get_prompt(self):
        return '%s@%s: %s> ' % (self.username, self.server, self.ftp.get_cwd())

    def proc_cli(self):
        ''' Process user input and translate them to appropriate ftp commands.
        '''
        while True:
            #print("|%s|" % self.get_prompt())
            try:
                cmd_line = input(self.get_prompt())
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

    readline.set_completer(Completer(get_ftp_commands()).complete)
    readline.parse_and_bind('tab: complete')

    cli = ftp_cli()
    try:
        cli.proc_input_args()
    except (cli_error):
        pass
    
