
import pytest

from bgpfu.client import IRRClient


def test_init():
    a = IRRClient()
    assert a
