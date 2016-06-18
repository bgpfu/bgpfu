
import logging
from pkg_resources import get_distribution
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

        if self.keepalive:
            self.sckt.send('!!\n')

        self.query('!nBGPFU-v%s\n' % get_distribution('bgpfu').version)

    def query(self, q):
        q = q + '\n'
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

        if state == 'C':
            return True

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


    def as_prefix(self, asn):
        print('!gAS%d' % int(asn))
        return self.query('!gAS%d' % int(asn)).split()
