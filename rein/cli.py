import json
import re
import os.path
import time
import click
import sqlite3
from subprocess import check_output

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.user import User, Base, create_account, import_account
 

db_filename = 'local.db'

engine = create_engine("sqlite:///%s" % db_filename)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

def yes_or_no(question):
    reply = str(input(question+' (y/n): ')).lower().strip()
    
    if len(reply) > 0 and reply[0] == 'y':
        return True
    if len(reply) > 0 and reply[0] == 'n':
        return False
    else:
        return yes_or_no("Please enter ")

#@click.option('--as-cowboy', '-c', is_flag=True, help='Greet as a cowboy.')
#@click.argument('name', default='world', required=False)
@click.group()
def cli():
    pass

@cli.command()
def main():
    '''Rein - decentralized professional services market'''
    click.echo("\nWelcome to Rein.\n")
    if not os.path.isfile(db_filename):
        click.echo("It looks like this is your first time running Rein on this computer.\n"\
                "Do you want to import a backup or create a new account?\n"\
                "1 - Import\n2 - Create\n")
        choice = 0
        while choice not in (1, 2):
            choice = click.prompt("Choice", type=int, default=2)
            if choice == 2:
                create_account(engine, session, name, contact)
            elif choice == 1:
                import_account(engine, session)
    else:
        bold = '\033[1m'
        regular = '\033[0m'
        click.echo("""Available commands:

    info
    sync
    post-job
    post-listing
    post-bid
    post-offer
    accept-bid
    post-work
    accept-work

For more info visit http://reinproject.org
                """)
