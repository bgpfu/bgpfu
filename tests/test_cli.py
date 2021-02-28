import pytest
from click.testing import CliRunner

import bgpfu.cli


def test_cli_invoke():
    runner = CliRunner()
    res = runner.invoke(bgpfu.cli.cli, ["as-set", "AS-20C"])
    print(res.output)
    assert res.output
    assert res.exit_code == 0

    res = runner.invoke(bgpfu.cli.cli, ["prefixlist", "AS-20C"])
    print(res.output)
    assert res.output
    assert res.exit_code == 0

    res = runner.invoke(bgpfu.cli.cli, ["raw", "!iAS-20C"])
    print(res.output)
    assert res.output
    assert res.exit_code == 0
