from ipaddress import ip_network

from bgpfu.prefixlist import PrefixSet


def test_prefixset_init_empty():
    ps = PrefixSet()
    assert ps is not None
    assert len(ps) == 0


def test_prefixset_init_meta():
    value = "test_value"
    ps = PrefixSet(meta=value)
    assert ps.meta("meta") == value
    assert ps.meta("atem") is None
    try:
        ps.meta("atem", strict=True)
    except Exception as e:
        assert isinstance(e, KeyError)
    assert isinstance(ps.meta(), dict) and len(ps.meta()) == 1


def test_prefixset_init_dict():
    data4 = {"ipv4": [{"prefix": "10.0.0.0/8", "greater-equal": 16, "less-equal": 24}]}
    data6 = {
        "ipv6": [{"prefix": "2001:db8::/32", "greater-equal": 48, "less-equal": 64}]
    }
    data = dict()
    data.update(data4)
    data.update(data6)
    dicts = (data4, data6, data)
    for d in dicts:
        ps = PrefixSet(d)
        assert ps


def test_prefixset_init_str():
    strings = ["10.0.0.0/8^16-24", "2001:db8::/32^48-64"]
    for s in strings:
        ps = PrefixSet(s)
        assert ps


def test_prefix_set_init_str_invalid():
    strings = ["10.0.0.1/8", "2000:g::/32", "10.0.0.0/8^8", ""]
    for s in strings:
        try:
            ps = PrefixSet(s)
        except Exception as e:
            assert isinstance(e, ValueError)


def test_prefixset_init_dict_invalid_af():
    dicts = [
        {"ipv5": [{"prefix": "10.0.0.0/8"}]},
        {"opv6": [{"prefix": "2001:db8::/32"}]},
    ]
    for d in dicts:
        ps = PrefixSet(d)
        assert len(ps) == 0


def test_prefixset_init_dict_invalid_prefix():
    dicts = [
        {"ipv4": [{"prefix": "10.0.0.1/8"}]},
        {"ipv6": [{"prefix": "2001:g::/32"}]},
    ]
    for d in dicts:
        ps = PrefixSet(d)
        assert len(ps) == 0


def test_prefixset_init_dict_af_mismatch():
    dicts = [
        {"ipv6": [{"prefix": "10.0.0.0/8", "greater-equal": 16, "less-equal": 24}]},
        {"ipv4": [{"prefix": "2001:db8::/32", "greater-equal": 48, "less-equal": 64}]},
    ]
    for d in dicts:
        ps = PrefixSet(d)
        assert len(ps) == 0


def test_prefixset_init_min_length_invalid():
    dicts = [
        {"ipv4": [{"prefix": "10.0.0.0/16", "greater-equal": 8, "less-equal": 16}]},
        {"ipv6": [{"prefix": "2001:db8::/48", "greater-equal": 32, "less-equal": 48}]},
    ]
    for d in dicts:
        ps = PrefixSet(d)
        assert len(ps) == 1


def test_prefixset_init_max_length_invalid():
    dicts = [
        {"ipv4": [{"prefix": "10.0.0.0/32", "greater-equal": 32, "less-equal": 48}]},
        {
            "ipv6": [
                {"prefix": "2001:db8::/128", "greater-equal": 128, "less-equal": 256}
            ]
        },
    ]
    for d in dicts:
        ps = PrefixSet(d)
        assert len(ps) == 1


def test_prefixset_init_length_missing():
    dicts = [
        {"ipv4": [{"prefix": "10.0.0.0/8"}]},
        {"ipv6": [{"prefix": "2001:db8::/32"}]},
    ]
    for d in dicts:
        ps = PrefixSet(d)
        assert len(ps) == 1


def test_prefixset_init_min_length_missing():
    dicts = [
        {"ipv4": [{"prefix": "10.0.0.0/8", "less-equal": 8}]},
        {"ipv6": [{"prefix": "2001:db8::/32", "less-equal": 32}]},
    ]
    for d in dicts:
        ps = PrefixSet(d)
        assert len(ps) == 1


def test_prefixset_init_max_length_missing():
    dicts = [
        {"ipv4": [{"prefix": "10.0.0.0/30", "greater-equal": 31}]},
        {"ipv6": [{"prefix": "2001:db8::/126", "greater-equal": 127}]},
    ]
    for d in dicts:
        ps = PrefixSet(d)
        assert len(ps) == 6


def test_prefixset_len():
    p4, l4, m4, n4 = "10.0.0.0", 8, 16, 24
    prefix4 = "%s/%d" % (p4, l4)
    p6, l6, m6, n6 = "2001:db8::", 32, 40, 48
    prefix6 = "%s/%d" % (p6, l6)
    e_count = 2 ** (n4 - l4 + 1) + 2 ** (n6 - l6 + 1) - 2 ** (m4 - l4) - 2 ** (m6 - l6)
    data = {
        "ipv4": [{"prefix": prefix4, "greater-equal": m4, "less-equal": n4}],
        "ipv6": [{"prefix": prefix6, "greater-equal": m6, "less-equal": n6}],
    }
    ps = PrefixSet(data)
    r_count = len(ps)
    assert e_count == r_count != 0


def test_prefixset_iter_prefixes():
    strings = ["10.0.0.0/8", "2001:db8::/32"]
    for s in strings:
        ps = PrefixSet(s)
        assert list(ps.prefixes()) == [ip_network(s)]


def test_prefixset_contains_prefix():
    strings = ["10.0.0.0/8", "2001:db8::/32"]
    for s in strings:
        ps = PrefixSet(s)
        assert ip_network(s) in ps


def test_prefixset_intersection():
    tuples = [
        ("10.0.0.0/8^16-24", "10.0.0.0/20"),
        ("2001:db8::/32^48-64", "2001:db8::/56"),
    ]
    for s1, s2 in tuples:
        ps1 = PrefixSet(s1)
        ps2 = PrefixSet(s2)
        assert list((ps1 & ps2).prefixes()) == [ip_network(s2)]


def test_prefixset_union():
    tuples = [("10.0.0.0/16", "10.1.0.0/16"), ("2001:db8::/48", "2001:db8:ffff::/48")]
    for s1, s2 in tuples:
        ps1 = PrefixSet(s1)
        ps2 = PrefixSet(s2)
        assert set((ps1 | ps2).prefixes()) == {ip_network(s1), ip_network(s2)}


def test_prefixset_data_no_aggr():
    data = {"ipv4": [{"prefix": "10.0.0.0/8"}], "ipv6": [{"prefix": "2001:db8::/32"}]}
    ps = PrefixSet(data)
    assert ps.data(aggregate=False) == data


def no_test_prefixset_data_aggr():
    """ Test broken from py3 conversion. """
    pre_data = {
        "ipv4": [
            {"prefix": "10.0.0.0/9"},
            {"prefix": "10.128.0.0/9"},
            {"prefix": "10.0.0.0/10"},
            {"prefix": "10.64.0.0/10"},
            {"prefix": "10.128.0.0/10"},
            {"prefix": "10.192.0.0/10"},
        ],
        "ipv6": [],
    }
    post_data = {
        "ipv4": [{"prefix": "10.0.0.0/8", "greater-equal": 9, "less-equal": 10}],
        "ipv6": [],
    }
    ps = PrefixSet(pre_data)
    assert ps.data(aggregate=True) == post_data


if __name__ == "__main__":
    test_prefixset_data_aggr()
