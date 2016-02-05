#import pytest
import click
from click.testing import CliRunner
from rein import cli
from rein.lib.validate import verify_sig


def test_post():
    runner = CliRunner()
    result = runner.invoke(cli.post, ['-d', 'tests/fixtures/post.form', '-n'])
    assert not result.exception
    assert result.exit_code == 0
    assert verify_sig(result.output)

def test_bid():
    runner = CliRunner()
    result = runner.invoke(cli.bid, ['--multi','--identity','Charlie','-d', 'tests/fixtures/bid.form', '-n'])
    print(result.output)
    verified = verify_sig(result.output)
    print(verified)
    assert not result.exception
    assert result.exit_code == 0
    assert verified['valid']
