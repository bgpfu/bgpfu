
import unittest
from bgpfu.client import IRRClient


class TestBGPFU(unittest.TestCase):
    def test_00_connect_irr():
        a = IRRClient()
        self.assertTrue(a)
