
import inspect
import ipaddress



class PrefixListBase(object):
    def __init__(self, prefix_ctor=ipaddress.ip_network, prefixes=None):
        self.prefix_ctor = prefix_ctor

    def make_prefix(self, prefix):
        return self.prefix_ctor(prefix)

    def add(self, prefix, meta={}):
        raise NotImplementedError("{} does not implement {}".format(
            self.__class__.__name__, inspect.currentframe().f_code.co_name))

    def iter_add(self, prefix, meta={}):
        raise NotImplementedError("{} does not implement {}".format(
            self.__class__.__name__, inspect.currentframe().f_code.co_name))
# TODO add get functions
