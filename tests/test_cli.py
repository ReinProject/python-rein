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
    sig_check(cli.bid, ['--multi','--identity','Charlie','-d', 'tests/fixtures/bid.form', '-n'])


def sig_check(function, args):
    runner = CliRunner()
    result = runner.invoke(function, args)
    print(result.output)
    verified = verify_sig(result.output.strip())
    print(verified)
    assert not result.exception
    assert result.exit_code == 0
    assert verified['valid']