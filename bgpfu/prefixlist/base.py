
import inspect
import ipaddress
from bgpfu.base import BaseObject


class PrefixListBase(BaseObject):
    def __init__(self, prefix_ctor=ipaddress.ip_network, prefixes=None, aggregate=True):
        super(PrefixListBase, self).__init__()
        self.prefix_ctor = prefix_ctor
        self.aggregate = aggregate

    def check_val(self, v):
        """ check value, call ctor if needed """
        if not isinstance(v, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
            return ipaddress.ip_network(unicode(v))
        return v

    def make_prefix(self, prefix):
        return self.prefix_ctor(prefix)

    def add(self, prefix, meta={}):
        raise NotImplementedError("{} does not implement {}".format(
            self.__class__.__name__, inspect.currentframe().f_code.co_name))

    def iter_add(self, prefix, meta={}):
        raise NotImplementedError("{} does not implement {}".format(
            self.__class__.__name__, inspect.currentframe().f_code.co_name))

    def str_list(self):
        raise NotImplementedError("{} does not implement {}".format(
            self.__class__.__name__, inspect.currentframe().f_code.co_name))

# TODO add get functions
