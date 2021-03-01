import os

import pytest

import bgpfu.roa
from bgpfu.roa import RoaTree


@pytest.fixture
def rpki_tree(this_dir):
    rpki_file = os.path.join(this_dir, "data", "rpki", "test0.json")
    return RoaTree(rpki_file=rpki_file)


def all_trees():
    this_dir = os.path.dirname(__file__)

    rpki_file = os.path.join(this_dir, "data", "rpki", "test0.json")
    rib_dir = os.path.join(this_dir, "data", "rib")
    rib_tree = RoaTree(rib_file=os.path.join(rib_dir, "test0-v4.txt"))
    rib_tree.load_rib_file(os.path.join(rib_dir, "test0-v6.txt"), merge=True)
    return [RoaTree(rpki_file=rpki_file), rib_tree]
    return [RoaTree(rpki_file=rpki_file)]


def test_roatree_init(this_dir):
    RoaTree()


def test_roatree_init_rib(this_dir):
    rib_file = os.path.join(this_dir, "data", "rib", "test0-v4.txt")
    rtree = RoaTree(rib_file=rib_file)


def test_roatree_init_rpki(this_dir):
    rpki_file = os.path.join(this_dir, "data", "rpki", "test0.json")
    rtree = RoaTree(rpki_file=rpki_file)


@pytest.mark.parametrize("tree", all_trees())
def test_roatree_validation(tree):
    args = ("192.0.2.0/24", 12345)
    state = tree.validation_state(*args)
    assert state["state"] == "valid"
    assert not tree.check_invalid(*args)

    args = ("192.0.2.0/24", 63311)
    state = tree.validation_state(*args)
    assert state["state"] == "valid"
    assert not tree.check_invalid(*args)

    args = ("192.0.2.0/24", 11336)
    state = tree.validation_state(*args)
    assert state["state"] == "invalid"
    assert tree.check_invalid(*args)

    args = ("2.0.0.0/24", 63311)
    state = tree.validation_state(*args)
    assert state["state"] == "notfound"
    assert not tree.check_invalid(*args)

    args = ("2001:db8::/32", 1)
    state = tree.validation_state(*args)
    assert state["state"] == "valid"
    assert not tree.check_invalid(*args)

    args = ("2002:db8::/32", 1)
    state = tree.validation_state(*args)
    assert state["state"] == "notfound"
    assert not tree.check_invalid(*args)

    args = ("2001:db8::/32", 63311)
    state = tree.validation_state(*args)
    assert state["state"] == "invalid"
    assert tree.check_invalid(*args)
