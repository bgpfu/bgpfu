import logging

import pytest

from bgpfu.client import IRRClient
from bgpfu.irr import IRRBase

logging.basicConfig(level=logging.DEBUG)


class IRRTest(IRRBase):
    pass


def do_impl_test(obj, func_name, *args, **kwargs):
    with pytest.raises(NotImplementedError):
        getattr(obj, func_name)(*args, **kwargs)


def test_base():
    obj = IRRTest()

    with obj as tst:
        pass

    do_impl_test(obj, "set_sources", "")
    do_impl_test(obj, "iter_sets", "")
    do_impl_test(obj, "get_sets", "")
    do_impl_test(obj, "iter_routes", "")
    do_impl_test(obj, "get_routes", "")
    do_impl_test(obj, "iter_prefixes", "")
    do_impl_test(obj, "get_prefixes", "")


def test_init():
    a = IRRClient()
    assert a


def test_queries():
    irr = IRRClient()
    with IRRClient() as irr:
        irr.set_sources("ARIN", "RIPE")
        iter_res = list(irr.iter_sets("AS-20C"))
        get_res = irr.get_sets("AS-20C")
        assert iter_res
        assert iter_res == get_res

        iter_res = list(irr.iter_routes("AS-20C"))
        get_res = irr.get_routes("AS-20C")
        #        assert iter_res
        assert iter_res == get_res

        iter_res = list(irr.iter_prefixes("AS-20C"))
        get_res = irr.get_prefixes("AS-20C")
        assert iter_res
        assert iter_res == get_res


def test_parse_response():
    irr = IRRClient()
    assert 175 == irr.parse_response("A175")
    assert not irr.parse_response("C")
    assert not irr.parse_response("C all ok")
    assert False == irr.parse_response("D")
    with pytest.raises(KeyError):
        irr.parse_response("E")
    with pytest.raises(RuntimeError) as excinfo:
        irr.parse_response("F unrecognized command")
    assert "unrecognized command" in str(excinfo.value)
