import logging
import inspect


class BaseObject(object):
    def __init__(self):
        self._log = logging.getLogger(self.__module__)

    def __repr__(self):
        return "%s() object" % self.cls_name

    def __enter__(self):
        self.log_ready_start()
        self.log_ready_done()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log_exit_start()
        self.log_exit_done()

    @property
    def opts(self):
        return getattr(self, "_opts", None)

    @property
    def log(self):
        return self._log

    @property
    def cls_name(self):
        return self.__class__.__name__

    @property
    def current_method(self):
        return inspect.currentframe().f_back.f_code.co_name

    def log_init(self):
        self.log.debug(msg="initialising %s instance" % self.cls_name)

    def log_init_done(self):
        caller = inspect.currentframe().f_back.f_back.f_code.co_name
        if caller == '__init__':
            self.log.debug(msg="still initialising %s instance" % self.cls_name)
        else:
            self.log.debug(msg="%s instance initialised" % self.cls_name)

    def log_method_enter(self, method=None):
        self.log.debug(msg="entering method %s.%s" % (self.cls_name, method))

    def log_method_exit(self, method=None):
        self.log.debug(msg="leaving method %s.%s" % (self.cls_name, method))

    def log_ready_start(self):
        self.log.debug(msg="preparing %s for use" % self)

    def log_ready_done(self):
        self.log.debug(msg="%s ready for use" % self)

    def log_exit_start(self):
        self.log.debug(msg="cleaning up %s" % self)

    def log_exit_done(self):
        self.log.debug(msg="finished cleaning up %s" % self)

    def raise_type_error(self, arg=None, cls=None):
        msg = "argument %s (%s) not of type %s" % (
            arg.__name__, arg, cls
            )
        self.log.error(msg=msg)
        raise TypeError(msg)

    def raise_runtime_error(self, msg=None):
        self.log.error(msg=msg)
        raise RuntimeError(msg)
