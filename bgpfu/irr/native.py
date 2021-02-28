# Copyright (C) 2016 Matt Griswold <grizz@20c.com>
#
# This file is part of bgpfu
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



from bgpfu.irr import IRRBase
from bgpfu.prefixlist import SimplePrefixList as PrefixList
from bgpfu.io import select, socket, Queue, Empty
import gevent
import logging
from pkg_resources import get_distribution
import re


class IRRClient(IRRBase):
    """
    IRR client, uses pipelining
        supports keepalive
    """
    def __init__(self):
        self.keepalive = True
        self.host = 'whois.radb.net'
        self.host = 'rr.ntt.net'
        self.port = 43

        self.re_res = re.compile('(?P<state>[ACDEF])(?P<len>\d*)(?P<msg>[\w\s]*)$')

        self.log = logging.getLogger(__name__)

        self.sckt = None
        self._send_queue = Queue()
        self._send_thread = None
        self._req_sent = 0

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, typ, value, traceback):
        self.sckt.shutdown(socket.SHUT_RDWR)
        self.sckt.close()
        self._send_thread.kill()
        self._send_thread.get()

    def connect(self):
        self.sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sckt.connect((self.host, self.port))
        self.sckt.setblocking(False)

        if self.keepalive:
            self.sckt.send('!!\n')

        self._send_thread = gevent.spawn(self._process_send_queue)

        self.query_one('!nBGPFU-{}'.format(get_distribution('bgpfu').version))

    def make_set_query(self, obj, expand=True):
        """
        if expand is true, also recursively expand members of all sets within the named set.
        """
        q = '!i' + obj
        if expand:
            q = q + ',1'
        return q

    def make_route_query(self, obj, proto=4):
        proto = int(proto)
        if proto == 4:
            return '!g' + obj
        elif proto == 6:
            return '!6' + obj

        raise ValueError("unknown protocol '%s'" % str(proto))

    def parse_response(self, response):
        self.log.debug("response %s", response)
        match = self.re_res.match(response)
        if not match:
            raise RuntimeError("invalid response '%s'" % (response,))

        state = match.group('state')
        if state == 'A':
            return int(match.group('len'))
        elif state == 'C':
            return False
        elif state == 'D':
            self.log.warning("skipping key not found")
            return False
        elif state == 'E':
            raise KeyError("multiple copies of key in database")
        elif state == 'F':
            if match.group('msg'):
                msg = match.group('msg').strip()
            else:
                msg = 'unknown error'
            raise RuntimeError(msg)

        raise RuntimeError("invalid response '%s'" % (response,))

    def iter_query(self, querylist):
        """
        performs a query, returns a generator
        """
        if not self.sckt:
            raise IOError("not connected")

        self.log.debug("QUERY {}".format(querylist))
        self._queue_query(querylist)
        gevent.sleep(.0001)
        for res in self._pipeline_read():
            yield res

    def query_one(self, query):
        """
        performs a query, checks for exactly 1 result, returns it
        """
        res = list(self.iter_query((query,)))

        if len(res) > 1:
            raise ValueError("query_one returned {} results".format(len(res)))

        elif len(res) == 1:
            return res[0]

        return None

    def query(self, querylist):
        """
        performs a query, returns a list
        """
        if isinstance(querylist, str):
            querylist = (querylist,)

        return list(self.iter_query(querylist))

    def _queue_query(self, querylist):
        if isinstance(querylist, str):
            querylist = (querylist,)
        # throw if queue is full
        self._send_queue.put_nowait(querylist)

    def _get_send_queue(self):
        max_chunk = 10
        idx = 0

        # force list, could be tuples on queue
        querylist = []
        # block until we get at least one
        querylist.extend(self._send_queue.get(True))

        # try to add any additional requests
        while True:
            try:
                if idx >= max_chunk:
                    break
                querylist.extend(self._send_queue.get_nowait())
                idx += 1

            except Empty:
                break
        return querylist

    def _process_send_queue(self):
        while True:
            self.log.debug("blocking on send queue")
            querylist = self._get_send_queue()

            qlen = len(querylist)
            self._req_sent += qlen
            # self.log.debug("sending {}/{}".format(qlen, self._req_sent))
            q = '\n'.join(querylist) + '\n'
            ttl = 0
            sz = len(q)
            while ttl < sz:
                sent = self.sckt.send(q[ttl:])
                if not sent:
                    raise RuntimeError("socket connection broken")
                ttl = ttl + sent

            self.log.debug("sent '{}' ]{}]".format(q.rstrip(), ttl))

    def _pipeline_read(self):
        if not self._req_sent:
            raise RuntimeError("read called without a queued request")

        reqno = 0
        buf = ''
        while reqno < self._req_sent:
            self.log.debug("processing {} of {}".format(reqno, self._req_sent))
            res, buf = self._read_res(buf)
            reqno += 1
            if not res:
                if self._req_sent == 1:
                    break
                continue
            yield res

        self._req_sent = 0

    def _read_res(self, buf=''):
        """
        read next response
        """
        chunks = []
        ttl = 0
        chunk_size = 4096

        # if we already have data, don't wait at all on the read
        if buf:
            timeout = 0
        else:
            timeout = 10

        chunk = ''
        readable = select.select([self.sckt], [], [], timeout)[0]

        if readable:
            chunk = self.sckt.recv(chunk_size)

#        self.log.debug("-- BUF -----\n{}------------".format(buf))
#        self.log.debug("-- CHUNK ---\n{}------------".format(chunk))
        if buf:
            chunk = buf + chunk

        idx = chunk.find('\n')
        if idx == -1:
            raise RuntimeError("no data to read, but no response in buffer")

        response = chunk[:idx]
        chunk = chunk[idx + 1:]

        sz = self.parse_response(response)
        if not sz:
            return None, chunk

        ttl = len(chunk)
        chunks.append(chunk)

        while ttl <= sz:
#            self.log.debug("ttl %d, sz %d", ttl, sz)
            readable = select.select([self.sckt], [], [])[0]
            if not readable:
                raise RuntimeError("socket connection broken")

            chunk = self.sckt.recv(chunk_size)

            if chunk == '':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            ttl = ttl + len(chunk)

        # slice off remaining buffer
        buf_sz = ttl - sz
        buf = chunks[-1][-buf_sz:]
        chunks[-1] = chunks[-1][:-buf_sz]

        # try to strip off command complete
        # FIXME - need to stop eating the last C on a result, it screws up the results
        buf = buf.lstrip('C')
        buf = buf.lstrip('\n')

        # self.log.debug("-- FINRES ---\n{}\n-- /FINRES ----".format(''.join(chunks)))
        # self.log.debug("-- FINBUF -----\n{}-- /FINBUF ----".format(buf))
        # self.log.debug("ttl %d, sz %d", ttl, sz)
        # self.log.debug("remaining %d '%s'", ttl - sz, buf)
        return ''.join(chunks), buf

    def set_sources(self, *sources):
        """ set sources to the specified list """
        res = self.query('!s{}'.format(','.join(sources)))
        # FIXME - stop eating the last C on a command
        # if len(res) != 1:
        #     raise RuntimeError("source query returned multiple results")

        # return res[0]
        return None

    def iter_sets(self, objs, expand=True):
        """
        Return members of an as-set or route-set.
        if expand is true, also recursively expand members of all sets within the named set.
        """
        if isinstance(objs, str):
            objs = (objs,)

        sets = []
        querylist = []

        for each in objs:
            q = '!i' + each
            if expand:
                q = q + ',1'
            self.log.debug("ADDING {}".format(q))
            querylist.append(q)

        self.log.debug("QUERLLLLLLL {}".format(querylist))
        for res in self.iter_query(querylist):
            sets += res.split()

        return set(sets)

    def iter_routes(self, obj, proto=4):
        """ get routes for specified object """
        proto = int(proto)
        if proto == 4:
            q = '!g'
        elif proto == 6:
            q = '!6'
        else:
            raise ValueError("unknown protocol '%s'" % str(proto))

        q += obj
        prefixes = []
        for res in self.iter_query((q,)):
            if res:
                yield res.split()

    def iter_prefixes(self, as_sets, proto=4):
        """ get prefix list for specified as-set(s) """
        if isinstance(as_sets, str):
            as_sets = (as_sets,)
        querylist = list(map(self.make_set_query, as_sets))

        # get routes for each AS SET, put directly onto send queue
        for res in self.iter_query(querylist):
            self._queue_query(list(map(self.make_route_query, res.split())))

        # FIXME - need better handoff to io thread
        gevent.sleep(.0001)

        # read results from all requests
        for res in self._pipeline_read():
            if res:
                yield res.split()
