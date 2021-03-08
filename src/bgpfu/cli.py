# Copyright (C) 2016 Matt Griswold <grizz@20c.com>
#
# This file is part of bgpfu
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import ipaddress
import logging

import click

import bgpfu.client
from bgpfu.output import Output
from bgpfu.prefixlist import SimplePrefixList as PrefixList
from bgpfu.prefixlist.set import PrefixSet

from .roa import RoaTree

# global output formatter
outfmt = Output()


def common_options(f):
    f = click.option("--debug", is_flag=True, default=False)(f)
    return f


def as_set_options(f):
    f = click.option(
        "--skip-as",
        help="comma separated list of ASNs to not include in results",
        default=False,
    )(f)
    return f


def output_options(f):
    f = click.option(
        "--output-format",
        "-f",
        help="output format",
        type=click.Choice(outfmt.available_formats),
        default="txt",
        show_default=True,
    )(f)
    f = click.option("--output", "-o", help="output file", default="-")(f)
    return f


@click.group()
# @common_options
@click.version_option()
@click.pass_context
def cli(ctx):
    pass


@cli.command()
@click.pass_context
# @connect_options
@common_options
@click.argument("prefix", nargs=1)
@click.argument("asn", nargs=1)
@click.option("--rib-file", help="use bgp rib file")
@click.option("--rpki-file", help="use rpki json file")
def check_roa(ctx, prefix, asn, rib_file, rpki_file, **kwargs):
    """ check roa for prefix """
    prefix = ipaddress.ip_network(prefix)
    asn = int(asn)

    if rib_file and rpki_file:
        raise ValueError("bgp-rib and rpki-json are mutually exclusive")

    if rib_file:
        db = RoaTree(rib_file=rib_file)

    if rpki_file:
        db = RoaTree(rpki_file=rpki_file)

    print(f"check_roa {prefix} {asn}")
    rv = db.validation_state(prefix, asn)
    print(rv)


@cli.command()
@click.pass_context
# @connect_options
@common_options
@click.argument("query", nargs=1)
def raw(ctx, query, **kwargs):
    """ raw irr query """
    if kwargs.get("debug", False):
        logging.basicConfig(level=logging.DEBUG)

    bgpfuc = bgpfu.client.IRRClient()
    with bgpfuc as c:
        data = c.query(query)
        print(data)


@cli.command()
@common_options
@as_set_options
@click.argument("as-set", nargs=-1)
@click.pass_context
def as_set(ctx, as_set, **kwargs):
    """ expand an as-set """
    if kwargs.get("debug", False):
        logging.basicConfig(level=logging.DEBUG)
    bgpfuc = bgpfu.client.IRRClient()
    with bgpfuc as c:
        sets = c.get_sets(as_set)

    print("\n".join(sets))


@cli.command()
# @connect_options
@common_options
@output_options
@click.option(
    "--aggregate/--no-aggregate",
    "-A",
    help="aggregate prefixes",
    is_flag=True,
    default=True,
)
@click.option("--sources", help="use only specified sources (default is all)")
@click.option("--4", "-4", "proto", help="use IPv4", flag_value="4", default=True)
@click.option("--6", "-6", "proto", help="use IPv6", flag_value="6")
@click.option("--fancy", help="use fancy set", flag_value=True)
@click.argument("as-set", nargs=-1)
@click.pass_context
def prefixlist(ctx, as_set, output, output_format, proto, **kwargs):
    """ get prefix list for specified as-sets """
    if kwargs.get("debug", False):
        logging.basicConfig(level=logging.DEBUG)

    if kwargs.get("fancy", 0):
        prefixes = PrefixSet(aggregate=kwargs["aggregate"])
    else:
        prefixes = PrefixList()
    bgpfuc = bgpfu.client.IRRClient()
    with bgpfuc as c:
        if kwargs.get("sources", False):
            c.set_sources(kwargs["sources"])
        #        prefixes = c.get_prefixes(as_set, proto)

        for chunk in c.iter_prefixes(as_set, proto):
            prefixes.iter_add(chunk)

        if not kwargs["fancy"] and kwargs["aggregate"]:
            prefixes = prefixes.aggregate()

        with click.open_file(output, "w") as fobj:
            outfmt.write(output_format, fobj, prefixes.str_list())

        print("LEN {}".format(len(prefixes)))
