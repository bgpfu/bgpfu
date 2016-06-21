
import collections
import ipaddress


def _try_combine(aggregate, current):
    'try combining and replacing the last element on the aggregate list'
    if aggregate and aggregate[-1]:
        supernet = aggregate[-1].supernet()
        if supernet == current.supernet():
            aggregate.pop()
            aggregate.append(supernet)
            return True
    return False


def _do_aggregate(prefixlist):
    if len(prefixlist) <= 1:
        return prefixlist
    prefixlist = sorted(prefixlist)

    # TODO check for default and skip it?

    aggregate = []
    while True:
        current = None
        for pfx in prefixlist:
            if not current:
                current = pfx
                continue

            if current.overlaps(pfx):
                continue

            # try joining 2
            supernet = current.supernet()
            print "super", supernet
            print "excluses", supernet.address_exclude(current)
            if supernet == pfx.supernet():
                current = supernet
                continue

            # try joining with last one pushed
            if _try_combine(aggregate, current):
                current = None
                continue

            # nothing to combine, shift
            aggregate.append(current)
            current = pfx

        if current:
            if not _try_combine(aggregate, current):
                aggregate.append(current)

        if len(aggregate) == len(prefixlist):
            return aggregate

        prefixlist = aggregate
        aggregate = []


class PrefixList(collections.MutableSequence):

    def __init__(self, prefixes=None):
        if prefixes:
            self._prefixes = map(ipaddress.ip_network, map(unicode, prefixes))
        else:
            self._prefixes = []

    def __getitem__(self, i):
        return self._prefixes[i]

    def __setitem__(self, i, v):
        if not isinstance(v, ipaddress._BaseNetwork):
            v = ipaddress.ip_network(unicode(v))
        self._prefixes[i] = v

    def insert(self, i, v):
        if not isinstance(v, ipaddress._BaseNetwork):
            v = ipaddress.ip_network(unicode(v))
        self._prefixes.insert(i, v)

    def __delitem__(self, i):
        del self._prefixes[i]

    def __len__(self):
        return len(self._prefixes)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._prefixes == other._prefixes
        raise TypeError('object not PrefixList type')

    def __str__(self):
        return str(self._prefixes)


    @property
    def ipv4(self):
        return [p for p in self._prefixes if p.version == 4]

    @property
    def ipv6(self):
        return [p for p in self._prefixes if p.version == 6]

    def str_list(self):
        return map(str, self._prefixes)

    def _do_aggregate(self):
        pass

    def aggregate(self):
        'returns a PrefixList containing the result of aggregating the list'

        if len(self._prefixes) == 1:
            return PrefixList(self._prefixes)

        #v4 = sorted(self._prefixes)
        v4 = [p for p in self._prefixes if p.version == 4]
        v6 = [p for p in self._prefixes if p.version == 6]

        v4 = _do_aggregate(v4)
        v6 = _do_aggregate(v6)
        return PrefixList(v4 + v6)


