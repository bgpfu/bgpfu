from __future__ import absolute_import
from __future__ import print_function

import click
import bgpfu.client
import logging


def common_options(f):
    f = click.option('--debug', is_flag=True, default=False)(f)
    return f


@click.group()
#@common_options
@click.version_option()
@click.pass_context
def cli(ctx):
    pass


@cli.command()
@click.pass_context
#@connect_options
@common_options
@click.argument('query', nargs=1)
def raw(ctx, query, **kwargs):
    """ raw irr query """
    if kwargs.get('debug', False):
        logging.basicConfig(level=logging.DEBUG)

    bgpfuc = bgpfu.client.IRRClient()
    with bgpfuc as c:
        data = c.query(query)
        print(data)


@cli.command()
@click.pass_context
#@connect_options
@common_options
@click.option('--sources', help='use only specified sources (default is all)')
@click.argument('as-set', nargs=-1)
def prefixlist(ctx, as_set, **kwargs):
    """ get prefix list for specified as-sets """
    if kwargs.get('debug', False):
        logging.basicConfig(level=logging.DEBUG)

    prefixes = set()
    bgpfuc = bgpfu.client.IRRClient()
    with bgpfuc as c:
        if kwargs.get('sources', False):
            c.set_sources(kwargs['sources'])

        all_sets = []
        for each in as_set:
            all_sets += c.get_set(each)

        for each in all_sets:
            prefixes |= set(c.prefix4(each))
        print("\n".join(sorted(prefixes)))


