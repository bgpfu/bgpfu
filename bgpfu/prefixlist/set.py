from __future__ import unicode_literals
import re
import ipaddress
from collections import Set
from operator import itemgetter
from bgpfu.base import BaseObject
from bgpfu.prefixlist import PrefixListBase


class PrefixSet(PrefixListBase, Set):
    def __init__(self, data=None, **kwargs):
        super(PrefixSet, self).__init__()
        self.log_init()
        # if we weren't given a dict, try and parse it out
        # as prefix/len^min-max into the expected dict structure
        if data is None:
            data = {}
        if not isinstance(data, dict):
            try:
                data = self.parse_prefix_range(expr=data)
            except ValueError as e:
                self.log.error(msg=e.message)
                raise e
        # save meta information
        self._meta = kwargs
        self.log.debug(msg="creating prefix sets")
        # create sets per address family to hold prefix range tuples as
        # lower and upper bounds for prefix indices
        self._sets = {'ipv4': set(), 'ipv6': set()}
        for af in data:
            # determine the ip address version that we're dealing with
            try:
                version = int(re.match(r'^ipv(4|6)', af).group(1))
            except (ValueError, AttributeError):
                self.log.warning(msg="invalid address-family %s" % af)
                continue
            self.log.debug(msg="adding %s prefixes to set" % af)
            # create a temporary list to hold index ranges
            temp = list()
            for entry in data[af]:
                # calculate the index of the base prefix
                # we'll be calulating a breadth-first index
                # of the CBT sub-tree rooted at this node
                try:
                    prefix, root = self.index_of(entry["prefix"])
                except ValueError as e:
                    self.log.warning(msg=e.message)
                    continue
                # check that the prefix has the correct address version
                if prefix.version != version:
                    self.log.warning(msg="prefix %s not of version %d" % (prefix, version))
                    continue
                # get the length of the base prefix and the maximum prefix length
                # for the given address family
                l = prefix.prefixlen
                h = prefix.max_prefixlen
                self.log.debug(msg="setting base index of prefix: %s = %d" % (prefix, root))
                # check if we have been given min and max prefix-lengths
                m_set = False
                try:
                    m = max(int(entry["greater-equal"]), l)
                    m_set = True
                except (KeyError, ValueError):
                    m = l
                self.log.debug(msg="min-length set to %d" % m)
                try:
                    n = min(int(entry["less-equal"]), h)
                except (KeyError, ValueError):
                    if m_set:
                        n = h
                    else:
                        n = m
                self.log.debug(msg="max-length set to %d" % n)
                self.log.debug(msg="traversing subtree from index %d" % root)
                # calculate the total depth of the iteration
                depth = n - l
                left = right = root
                for d in range(0, depth + 1):
                    # check whether we're yet at the depth corresponding to the
                    # minimum prefix-length provided
                    if d >= m - l:
                        # add a tuple giving the lower and upper bounds of the
                        # indices of the subtree's nodes at this level
                        temp.append((left, right + 1))
                        self.log.debug(msg="added %d indices at depth %d" % (left - right + 1, d))
                    # get the lower and upper bounds at the next level
                    left *= 2
                    right = 2*right + 1
                self.log.debug(msg="indexing %s^%d-%d complete" % (prefix, m, n))
            # sort temp list by lower bound values
            temp.sort(key=itemgetter(1))
            # get reference to the correct set
            s = self.sets(af)
            # loop through the resulting range entries and
            # merge into the smallest set of entries
            lower, upper = None, None
            for next_lower, next_upper in temp:
                if lower is None:
                    lower = next_lower
                    upper = next_upper
                    continue
                if upper < next_lower:
                    s.add((lower, upper))
                    lower = next_lower
                upper = next_upper
            else:
                if upper is not None:
                    s.add((lower, upper))
        self.log_init_done()

    def __contains__(self, item):
        if isinstance(item, tuple):
            version = item[0]
            index = item[1]
        else:
            try:
                prefix, index = self.index_of(prefix=item)
            except ValueError as e:
                self.log.error(msg=e.message)
                raise e
            version = prefix.version
        for lower, upper in self.sets(version):
            if lower <= index < upper:
                return True
        return False

    def __iter__(self):
        for version in (4, 6):
            for lower, upper in self.sets(version):
                index = lower
                while index < upper:
                    yield (version, index)
                    index += 1

    def __len__(self):
        count = 0
        for version in (4, 6):
            for lower, upper in self.sets(version):
                count += upper - lower
        return count

    def _iter_ranges(self):
        for version in (4, 6):
            for lower, upper in self.sets(version):
                yield (version, lower, upper)

    def __and__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        it = list()
        for i_version, i_lower, i_upper in other._iter_ranges():
            for j_version, j_lower, j_upper in self._iter_ranges():
                if i_version == j_version:
                    v = i_version
                    l = max(i_lower, j_lower)
                    u = min(i_upper, j_upper)
                    if l <= u:
                        it.append((v, l, u))
        return self._from_iterable(it)

    def __or__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return super(PrefixSet, self).__or__(other)

    @classmethod
    def _from_iterable(cls, it):
        self = cls({})
        for item in it:
            af = "ipv%d" % item[0]
            lower = item[1]
            try:
                upper = item[2]
            except IndexError:
                upper = lower + 1
            try:
                self.sets(af).add((lower, upper))
            except KeyError as e:
                self.log.error(msg=e.message)
                raise e
        return self

    def iter_add(self, it):
        for item in it:
            prefix = self.check_val(item)
            af = "ipv%d" % prefix.version
            lower = item[1]
            try:
                upper = item[2]
            except IndexError:
                upper = lower + 1
            try:
                self.sets(af).add((lower, upper))
            except KeyError as e:
                self.log.error(msg=e.message)
                raise e
        return self

    def sets(self, af=None):
        try:
            return self._sets[af]
        except KeyError as e:
            try:
                return self._sets["ipv%d" % af]
            except KeyError as f:
                self.log.warning(msg=e.message)
                self.log.error(msg=f.message)
                raise f

    def prefixes(self):
        for version, index in self:
            yield self.indexed_by(index=index, af="ipv%d" % version)

    def meta(self, key=None, strict=False):
        if key:
            try:
                return self._meta[key]
            except KeyError as e:
                if strict:
                    self.log.error(msg=e.message)
                    raise e
                else:
                    self.log.debug(msg=e.message)
                    return None
        else:
            return self._meta

    @staticmethod
    def index_of(prefix=None):
        prefix = ipaddress.ip_network(prefix)
        p = int(prefix.network_address)
        l = prefix.prefixlen
        h = prefix.max_prefixlen
        index = 2**l + p/2**(h - l)
        return prefix, index

    @staticmethod
    def indexed_by(index=None, af=None):
        address_families = {
            'ipv4': {'size': 32, 'cls': ipaddress.IPv4Network},
            'ipv6': {'size': 128, 'cls': ipaddress.IPv6Network}
        }
        assert isinstance(index, (int, long))
        assert af in address_families
        h = int(address_families[af]['size'])
        cls = address_families[af]['cls']
        l = index.bit_length() - 1
        p = index * 2**(h - l) - 2**h
        return cls((p, l))

    @staticmethod
    def parse_prefix_range(expr=None):
        pattern = r'^(?P<prefix>((\d+(\.\d+){3})|([0-9a-fA-F:]{2,40}))/\d+)' \
                  r'(\^(?P<ge>\d+)-(?P<le>\d+))?$'
        match = re.match(pattern, expr)
        if match:
            prefix = ipaddress.ip_network(unicode(match.group("prefix")))
            afi = "ipv%d" % prefix.version
            entry = {"prefix": prefix}
            try:
                entry["greater-equal"] = int(match.group("ge"))
                entry["less-equal"] = int(match.group("le"))
            except (IndexError, TypeError):
                pass
        else:
            raise ValueError("no match found")
        return {afi: [entry]}
