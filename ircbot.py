import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr

# a better basic IRC Bot blank-canvas
# based on https://github.com/jaraco/irc/blob/main/scripts/testbot.py
# using jaraco/irc

owner_vhost = '@op.shadowsword.ca'
CH          = "#journey,#fuar"
NICK        = "ShadowServ"
ADDR        = '127.0.0.1'

class ShadowServ(irc.bot.SingleServerIRCBot):
    
    # Initialize Server Connection Here.
    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel

    # Nick In Use
    def on_nicknameinuse(self, connection, event):
        print('nick conflict')
        connection.nick(connection.get_nickname() + "_")

    # Connection Welcome => Join Channel (?)
    def on_welcome(self, connection, event):
        print(f'on_welcome: {connection} {event}')
        connection.join(self.channel)

    # DM/PRIVMSG
    def on_privmsg(self, connection, event):
        self.do_command(event, event.arguments[0])

    # Channel Message
    def on_pubmsg(self, connection, event):
        pub_cmd = event.arguments[0].split(":", 1)
        if len(pub_cmd) > 1 and irc.strings.lower(pub_cmd[0]) == irc.strings.lower(
            self.connection.get_nickname()
        ):
            self.do_command(event, pub_cmd[1].strip())
        return

    def do_command(self, event, cmd):
        # bool: pubmsg or privmsg?
        public = (True if event.type == 'pubmsg' else False)
        nick = event.source.nick    # source nick
        nick_oper = False           # (default) bool: is chan oper
        c = self.connection         # connection
        ch = event.target           # #channel or nick
        ch_opers = ['']             # (default) list: chan opers
        # owner = @op.shadowsword.ca
        owner = self.ownership_check(event)
        
        if public:
            nick_oper = self.channels[ch].is_oper(nick)
            ch_opers = sorted(self.channels[ch].opers())
        
        print(f'👋 think: {cmd} (owner: {owner}) (op: {nick_oper}) (ch: {ch}) (chops: {ch_opers})')

        #############################
        # ALL COMMANDS ENABLED HERE!
        commands = {
            
            'public': {
                'die': self.do_die,
                'chanstats': self.do_chanstats,
                'stats': self.do_stats,
                'debug': self.do_debug,
            },

            'private': {
                'die': self.do_die,
                'stats': self.do_stats,
                'debug': self.do_debug,
            }

        }
        #############################

        if public:
            available_commands = commands['public']
        else:
            available_commands = commands['private']

        try:
            available_commands[cmd](event, cmd)
        except KeyError:
            self.error_exec_command(event, cmd)
        
    def do_stats(self, event, cmd):
        for chname, chobj in self.channels.items():
            self.notice(event, "--- Channel statistics ---")
            self.notice(event, "Channel: " + chname)
            users = sorted(chobj.users())
            self.notice(event, "Users: " + ", ".join(users))
            opers = sorted(chobj.opers())
            self.notice(event, "Opers: " + ", ".join(opers))
            #voiced = sorted(chobj.voiced())
            #self.notice(event, "Voiced: " + ", ".join(voiced))
        return

    def do_chanstats(self, event, cmd):
        ch = event.target
        users = sorted(self.channels[ch].users())
        opers = sorted(self.channels[ch].opers())
        return self.notice(event, f'Channel {ch}: Users: {", ".join(users)}; Opers: {", ".join(opers)}')

    def do_die(self, event, cmd):
        '''Kill the bot process, requires ownership vhost'''
        owner = self.ownership_check(event)
        if owner:
            return self.die(msg="Bah! You killed me sir! Goodbye!")
        else:
            return self.error_exec_command(event, cmd)
    
    def do_debug(self, event, cmd):
        print(self.connection.__dict__)
        return

    def ownership_check(self, event):
        '''Return True if @op.shadowsword.ca'''
        global owner_vhost
        return (True if event.source.endswith(owner_vhost) else False)
        
    def res(self, event, response=''):
        '''Respond appropriately based on target'''
        c = self.connection
        ch = event.target
        nick = event.source.nick

        if event.type == 'pubmsg':
            return c.privmsg(ch, response)
        else:
            return c.notice(nick, response)
    
    def notice(self, event, response=''):
        '''Force Notice even if on public channel for notice driven command (better for lag)'''
        c = self.connection
        nick = event.source.nick
        return c.notice(nick, response)

    def error_exec_command(self, event, cmd):
        '''Default Error Handler'''
        error_message = f'Sorry, the command [{cmd}] could not be run.'
        if event.type == 'pubmsg':
            return self.connection.privmsg(event.target, error_message)
        elif event.type == 'privmsg':
            return self.connection.notice(event.source.nick, error_message)

BOT  = ShadowServ("#journey,#sparring,#fuar",NICK,ADDR).start()
