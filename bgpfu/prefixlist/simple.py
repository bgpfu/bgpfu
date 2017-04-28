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

import collections
import ipaddress

from bgpfu.prefixlist import PrefixListBase


def _try_combine(aggregate, current):
    'try combining and replacing the last element on the aggregate list'
    if aggregate and aggregate[-1]:
        supernet = aggregate[-1].supernet()
        if supernet == current.supernet():
            aggregate[-1] = supernet
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
            if supernet == pfx.supernet():
                current = supernet
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


class SimplePrefixList(PrefixListBase, collections.MutableSequence):
    """
    Simple PrefixList implemenatation using collections
    *NOTE* loses prefix length info on aggregate
    """
    def __init__(self, prefixes=None):
        if prefixes:
            self._prefixes = map(ipaddress.ip_network, map(unicode, prefixes))
        else:
            self._prefixes = []

    def __getitem__(self, i):
        return self._prefixes[i]

    def __setitem__(self, i, v):
        self._prefixes[i] = self.check_val(v)

    def insert(self, i, v):
        self._prefixes.insert(i, self.check_val(v))

    def iter_add(self, it):
        for v in it:
            self._prefixes.append(self.check_val(v))

    def __delitem__(self, i):
        del self._prefixes[i]

    def __len__(self):
        return len(self._prefixes)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._prefixes == other._prefixes
        raise TypeError('object not PrefixList type')

    def __ne__(self, other):
        return not self == other

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

    def aggregate(self):
        'returns a PrefixList containing the result of aggregating the list'

        if len(self._prefixes) == 1:
            return self.__class__(self._prefixes)

        #v4 = sorted(self._prefixes)
        v4 = [p for p in self._prefixes if p.version == 4]
        v6 = [p for p in self._prefixes if p.version == 6]

        v4 = _do_aggregate(v4)
        v6 = _do_aggregate(v6)
        return self.__class__(v4 + v6)

