
import pytest

from bgpfu.client import IRRClient


def test_init():
    a = IRRClient()
    assert a

def test_parse_response():
    irr = IRRClient()
    assert 175 == irr.parse_response('A175')
    assert not irr.parse_response('C')
    assert not irr.parse_response('C all ok')
    assert False == irr.parse_response('D')
    with pytest.raises(KeyError):
        irr.parse_response('E')
    with pytest.raises(RuntimeError) as e:
        irr.parse_response('F unrecognized command')
    assert "unrecognized command" == e.value.message

