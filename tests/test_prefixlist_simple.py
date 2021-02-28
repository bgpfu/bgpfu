import ipaddress

import pytest

from bgpfu.prefixlist import SimplePrefixList as PrefixList

prefixes0 = [
    "2620::/64",
    "10.0.0.0/20",
    "1.0.1.0/24",
    "20.0.1.0/24",
    "192.1.0.0/24",
    "::/0",
]


def test_prefixlist_init():
    PrefixList()

    pfx = PrefixList(prefixes0)

    assert 4 == len(pfx.ipv4)
    assert 2 == len(pfx.ipv6)
    assert 6 == len(pfx)


def test_prefixlist_eq():
    pfx0 = PrefixList(prefixes0)
    pfx1 = PrefixList(prefixes0)
    assert pfx0 == pfx1

    pfx1.pop()
    assert pfx0 != pfx1

    with pytest.raises(TypeError) as excinfo:
        pfx0 != "string"
    assert "object not PrefixList type" in str(excinfo.value)

    with pytest.raises(TypeError) as excinfo:
        pfx0 != "string"
    assert "object not PrefixList type" in str(excinfo.value)


def test_prefixlist_append():
    pfx0 = PrefixList(prefixes0)
    pfx1 = PrefixList()

    for each in prefixes0:
        pfx1.append(each)

    print(pfx0)
    print(pfx1)
    assert pfx0 == pfx1


def test_prefixlist_append():
    pfx0 = PrefixList(prefixes0)
    pfx1 = PrefixList()

    for each in prefixes0:
        pfx1.append(each)

    print(pfx0)
    print(pfx1)
    assert pfx0 == pfx1


def test_prefixlist_set():
    pfx0 = PrefixList(prefixes0)
    pfx1 = PrefixList(prefixes0)
    assert pfx0 == pfx1

    idx = len(prefixes0) - 1
    pfx1[idx] = prefixes0[idx]
    assert pfx0 == pfx1

    pfx1[idx] = pfx0[idx]
    assert pfx0 == pfx1


# FIXME - should check values and not object refs
#    pfx1[idx] = ipaddress.ip_network(prefixes0[idx])
#    assert pfx0 == pfx1


def test_prefixlist_str_list():
    pfx0 = PrefixList(prefixes0)
    assert prefixes0 == pfx0.str_list()


def test_aggregate_single():
    prefixlist = [
        "10.0.1.0/24",
    ]
    expected = [
        "10.0.1.0/24",
    ]
    pfx = PrefixList(prefixlist)

    assert expected == pfx.aggregate().str_list()
    assert PrefixList(prefixlist) == pfx


def test_aggregate_super():
    prefixlist = [
        "10.0.1.0/24",
        "10.0.0.0/20",
        "2001:db8::/32",
        "2001:db8:1::/64",
    ]
    expected = [
        "10.0.0.0/20",
        "2001:db8::/32",
    ]
    pfx = PrefixList(prefixlist)

    assert expected == pfx.aggregate().str_list()
    assert PrefixList(prefixlist) == pfx


def test_aggregate_combine():
    prefixlist = [
        "10.0.0.0/24",
        "10.0.1.0/24",
    ]
    expected = [
        "10.0.0.0/23",
    ]
    pfx = PrefixList(prefixlist)

    assert expected == pfx.aggregate().str_list()
    assert PrefixList(prefixlist) == pfx


def test_aggregate_combine_multi():
    prefixlist = [
        "10.0.0.0/24",
        "10.0.1.0/24",
        "10.0.2.0/23",
    ]
    expected = [
        "10.0.0.0/22",
    ]

    pfx = PrefixList(prefixlist)

    assert expected == pfx.aggregate().str_list()
    assert PrefixList(prefixlist) == pfx


def test_aggregate_combine_multimore():
    prefixlist = [
        "10.0.0.0/24",
        "10.0.1.0/24",
        "10.0.2.0/23",
        "10.0.4.0/24",
        "10.0.5.0/24",
        "10.0.6.0/24",
        "10.0.7.0/24",
    ]
    expected = [
        "10.0.0.0/21",
    ]

    pfx = PrefixList(prefixlist)

    assert expected == pfx.aggregate().str_list()
    assert PrefixList(prefixlist) == pfx


def test_aggregate_combine_default():
    prefixlist = [
        "10.0.0.0/24",
        "10.0.1.0/24",
        "10.0.2.0/23",
        "0.0.0.0/0",
    ]
    expected = [
        "0.0.0.0/0",
    ]

    pfx = PrefixList(prefixlist)

    assert expected == pfx.aggregate().str_list()
    assert PrefixList(prefixlist) == pfx
