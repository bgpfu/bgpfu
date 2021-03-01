import os

import pytest


def _this_dir():
    """
    returns dirname for location of this file
    py.test no longer allows fixtures to be called
    directly so we provide a private function that can be
    """
    return os.path.dirname(__file__)


@pytest.fixture
def this_dir():
    return _this_dir()
