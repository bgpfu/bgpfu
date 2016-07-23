
import pytest
from click.testing import CliRunner

import bgpfu.cli


def test_cli_invoke():
    runner = CliRunner()
    res = runner.invoke(bgpfu.cli.cli, ['as_set'])
    res = runner.invoke(bgpfu.cli.cli, ['prefixlist'])
    res = runner.invoke(bgpfu.cli.cli, ['raw'])

