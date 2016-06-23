from __future__ import absolute_import
from __future__ import print_function

import click
import bgpfu.client
import logging


def get_output_formats():
    # TODO pkg_resource ls and plugins?
    return ('cisco_ios', 'cisco_iox', 'juniper', 'txt')


def common_options(f):
    f = click.option('--debug', is_flag=True, default=False)(f)
    return f


def as_set_options(f):
    f = click.option('--skip-as', help='comma separated list of ASNs to not include in results', default=False)(f)
    return f


def output_options(f):
    f = click.option('--output-format', '-f', help='output format', type=click.Choice(get_output_formats()), default='txt', show_default=True)(f)
    f = click.option('--output', '-o', help='output file', default='-')(f)
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
@common_options
@as_set_options
@click.argument('as-set', nargs=-1)
@click.pass_context
def as_set(ctx, as_set, **kwargs):
    """ expand an as-set """
    if kwargs.get('debug', False):
        logging.basicConfig(level=logging.DEBUG)
    bgpfuc = bgpfu.client.IRRClient()
    with bgpfuc as c:
        sets = c.get_set(as_set)

    print("\n".join(sets))


@cli.command()
#@connect_options
@common_options
@output_options
@click.option('--aggregate/--no-aggregate', '-A', help='aggregate prefixes', is_flag=True, default=True)
@click.option('--sources', help='use only specified sources (default is all)')
@click.option('--4', '-4', 'proto', help="use IPv4", flag_value='4', default=True)
@click.option('--6', '-6', 'proto', help='use IPv6', flag_value='6')
@click.argument('as-set', nargs=-1)
@click.pass_context
def prefixlist(ctx, as_set, output, proto, **kwargs):
    """ get prefix list for specified as-sets """
    if kwargs.get('debug', False):
        logging.basicConfig(level=logging.DEBUG)

    prefixes = set()
    bgpfuc = bgpfu.client.IRRClient()
    with bgpfuc as c:
        if kwargs.get('sources', False):
            c.set_sources(kwargs['sources'])
        prefixes = c.prefixlist(as_set, proto)

        if kwargs.get('aggregate', True):
            prefixes = prefixes.aggregate()

        with click.open_file(output, 'w') as fobj:
            if kwargs['output_format'] == 'txt':
                fobj.write('\n'.join(prefixes.str_list()))
                fobj.write('\n')

