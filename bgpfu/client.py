
import logging
import re
import socket


class IRRClient(object):

    def __init__(self):
        self.keepalive = True
        self.host = 'whois.radb.net'
        self.host = 'rr.ntt.net'
        self.port = 43

        self.re_res = re.compile('(?P<state>[ACD])(?P<len>\d+)$')

        self.log = logging.getLogger(__name__)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        self.sckt.shutdown(socket.SHUT_RDWR)
        self.sckt.close()

    def connect(self):
        self.sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sckt.connect((self.host, self.port))
        self.sckt.send('!nBGPFU-v%s\n' % __version__)
        if self.keepalive:
            self.sckt.send('!!\n')

    def query(self, q):
        ttl = 0
        sz = len(q)
        while ttl < sz:
            sent = self.sckt.send(q[ttl:])
            if not sent:
                raise RuntimeError("socket connection broken")
            ttl = ttl + sent

        self.log.debug("sent %s %d", q.rstrip(), ttl)

        chunks = []
        ttl = 0
        chunk_size = 4096

        chunk = self.sckt.recv(chunk_size)
        state, chunk = chunk.split('\n', 1)
        self.log.debug("state %s", state)
        match = self.re_res.match(state)
        if not match:
            raise RuntimeError("invalid response '%s'" % (chunk,))

        sz = int(match.group('len'))
        ttl = len(chunk)
        chunks.append(chunk)

        while ttl <= sz:
            self.log.debug("ttl %d, sz %d", ttl, sz)
            chunk = self.sckt.recv(chunk_size)
            if chunk == '':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            ttl = ttl + len(chunk)
#            self.log.debug("ttl %d, sz %d", ttl, sz)
#            self.log.debug("chunk '%s'", chunk)

        # split data from response code
        self.log.debug("ttl %d, sz %d", ttl, sz)
        suffix = chunks[-1][-(ttl - sz):]
        chunks[-1] = chunks[-1][:-(ttl - sz)]
        self.log.debug("suffix %d '%s'", ttl - sz, suffix)
        return ''.join(chunks)

