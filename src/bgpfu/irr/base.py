import inspect


class IRRBase:
    """
    Base class for performing IRR queries
    """

    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        pass

    def set_sources(self, *sources):
        """ set sources to the specified list """
        raise NotImplementedError(
            "{} does not implement {}".format(
                self.__class__.__name__, inspect.currentframe().f_code.co_name
            )
        )

    def iter_sets(self, objs, expand=True):
        """
        Return members of an as-set or route-set.
        if expand is true, also recursively expand members of all sets within the named set.
        """
        raise NotImplementedError(
            "{} does not implement {}".format(
                self.__class__.__name__, inspect.currentframe().f_code.co_name
            )
        )

    def get_sets(self, objs, expand=True):
        """
        Return members of an as-set or route-set.
        if expand is true, also recursively expand members of all sets within the named set.
        """
        return list(self.iter_sets(objs, expand))

    def iter_routes(self, objs, proto=4):
        """ get routes for specified object """
        raise NotImplementedError(
            "{} does not implement {}".format(
                self.__class__.__name__, inspect.currentframe().f_code.co_name
            )
        )

    def get_routes(self, objs, proto=4):
        """ get routes for specified object """
        return list(self.iter_routes(objs, proto))

    def iter_prefixes(self, as_sets, proto=4):
        """
        get prefix list for specified as-set(s)
        """
        raise NotImplementedError(
            "{} does not implement {}".format(
                self.__class__.__name__, inspect.currentframe().f_code.co_name
            )
        )

    def get_prefixes(self, as_sets, proto=4):
        """
        get prefix list for specified as-set(s)
        """
        return list(self.iter_prefixes(as_sets, proto))
