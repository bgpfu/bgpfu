
import pytest
from bgpfu.output import Output


def test_available():
    output = Output()
    assert ['juniper', 'txt'] == output.available_formats

def test_load_file():
    output = Output()
    assert output.load_file('templates/juniper.j2')

