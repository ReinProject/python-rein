import json
import re
import os
import time
import click
import sqlite3
from subprocess import check_output

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.user import User, Base, create_account, import_account
from lib.validate import enroll
import lib.config as config

config_dir = os.path.join(os.path.expanduser('~'), '.rein')
db_filename = 'local.db'

if not os.path.isdir(config_dir):
    os.mkdir(config_dir)

engine = create_engine("sqlite:///%s" % os.path.join(config_dir, db_filename))
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

#@click.option('--as-cowboy', '-c', is_flag=True, help='Greet as a cowboy.')
#@click.argument('name', default='world', required=False)
@click.group()
def cli():
    pass

@cli.command()
def main():
    '''Rein - decentralized professional services market'''
    click.echo("\nWelcome to Rein.\n")
    if not os.path.isfile(db_filename) or session.query(User).count() == 0:
        click.echo("It looks like this is your first time running Rein on this computer.\n"\
                "Do you want to import a backup or create a new account?\n"\
                "1 - Create new account\n2 - Import backup\n")
        choice = 0
        user = None
        while choice not in (1, 2):
            choice = click.prompt("Choice", type=int, default=1)
            if choice == 1:
                user = create_account(engine, session)
            elif choice == 2:
                user = import_account(engine, session)
        click.echo("------------")
        click.echo("The file %s has just been saved with your user details and needs to be signed "\
                "with your master Bitcoin private key. The private key for this address should be "\
                "kept offline and multiple encrypted backups made. This key will effectively "\
                "become your identity in Rein and a delegate address will be used for day to day "\
                "transactions.\n\n" % config.enroll_filename)
        res = enroll(user)
        if res['valid']:
            if click.confirm("Signature verified. Would you like to choose some microhosting servers?"):
                upload()
            else:
                click.echo("Signature stored. Run 'rein --upload' to continue with upload to microhosting.")
    else:
        bold = '\033[1m'
        regular = '\033[0m'
        click.echo("""Available commands:

    info, sync, post-job, post-listing, post-bid, post-offer, accept-bid, post-work, accept-work

For more info visit http://reinproject.org
                """)

@cli.command()
def upload():
    servers = ['http://bitcoinexchangerate.org/causeway']
    for server in servers:
        url = '%s%s' % (server, '/info.json')
        text = check_output('curl',url)
        try:
            data = json.loads(text)
        except:
            raise RuntimeError('Problem contacting server %s' % server)

        click.echo('%s - %s BTC' % (server, data['price']))
