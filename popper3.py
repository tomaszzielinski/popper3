#!/usr/bin/python
# http://www.faqs.org/rfcs/rfc1939.html
# http://docs.python.org/release/2.6.1/library/socketserver.html

import SocketServer
import multiprocessing 
import mailbox

import daemon

class MyTCPHandler(SocketServer.StreamRequestHandler):
    """
    From http://docs.python.org/library/socketserver.html#socketserver-tcpserver-example:
      It is instantiated once per connection to the server, and must
      override the handle() method to implement communication to the
      client.
    """

    def respond(self, s):
        self.wfile.write(s + '\r\n')
        print s.strip()

    def handle(self):
        self.wfile.write('+OK POP3 server ready\r\n')
        pid = multiprocessing.current_process().pid
        print "Connected (pid=%d)" % pid
        
        mbox = mailbox.mbox('/var/mail/root', create=False)

        while True:
            full_cmd = self.rfile.readline().strip()
            full_cmdsplit = full_cmd.split(None, 1)
            cmd = param = ''
            if len(full_cmdsplit) >= 1:
                cmd = full_cmdsplit[0]
            if len(full_cmdsplit) == 2:
                param = full_cmdsplit[1]
            
            print "Client cmd (pid=%d): '%s|%s'" % (pid, cmd, param)

            if cmd == 'QUIT':
                self.respond('+OK Terminating')
                break
            elif cmd == 'CAPA':
                self.respond('+OK')
                self.respond('UIDL')
                self.respond('.')
            elif cmd == 'USER':
                self.respond('+OK User "%s" accepted' % param)
            elif cmd == 'PASS':
                self.respond('+OK Password "%s" accepted' % param)
            elif cmd == 'STAT':
                num_messages = len(mbox)
                total_size = sum([len(msg.as_string()) for msg in mbox.values()])
                self.respond('+OK %d %d' % (num_messages, total_size))
            elif cmd == 'LIST' and not param:
                self.respond('+OK')
                for msg_id, msg in mbox.iteritems():
                    self.respond('%d %d' % (msg_id + 1, len(msg.as_string())))
                self.respond('.')
            elif cmd == 'RETR':
                self.respond('+OK')
                msg_id = int(param) - 1
                self.respond(mbox[msg_id].as_string())
                self.respond('.')
            elif cmd == 'DELE':
                self.respond('+OK') # Fake deletion
            elif cmd == 'UIDL' and not param:
                self.respond('+OK')
                for msg_id, msg in mbox.iteritems():
                    self.respond('%d %d-%s' % (msg_id + 1, msg_id+1, hash(msg.as_string())))
                self.respond('.')
            elif cmd == 'UIDL' and param:
                msg_id = int(param) - 1
                msg_hash = '%d-%s' % (msg_id, hash(mbox[msg_id].as_string()))
                self.respond('+OK %d %s' % (msg_id, msg_hash))
            else:
                self.respond('-ERR')

if __name__ == "__main__":
    with daemon.DaemonContext():
        server = SocketServer.TCPServer(("127.0.0.1", 9999), MyTCPHandler)
        server.serve_forever()
