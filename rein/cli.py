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
from lib.validate import validate_enrollment
import lib.config as config

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
    if not os.path.isfile(db_filename) or session.query(User).count() == 0:
        click.echo("It looks like this is your first time running Rein on this computer.\n"\
                "Do you want to import a backup or create a new account?\n"\
                "1 - Import backup\n2 - Create new account\n")
        choice = 0
        user = None
        while choice not in (1, 2):
            choice = click.prompt("Choice", type=int, default=2)
            if choice == 2:
                user = create_account(engine, session)
            elif choice == 1:
                user = import_account(engine, session)
        click.echo("------------")
        click.echo("The file %s has just been saved with your user details and needs to be signed "\
                "with your master Bitcoin private key. The private key for this address should be "\
                "kept offline and multiple encrypted backups made. This key will effectively "\
                "become your identity in Rein and a delegate address will be used for day to day "\
                "transactions.\n\n" % config.enroll_filename)
        enrollment = "Rein User Enrollment\nUser: %s\nContact: %s\nMaster signing address: %s\n" % (user.name, user.contact, user.maddr)
        f = open(config.enroll_filename, 'w')
        f.write(enrollment)
        f.close()
        click.echo("\n%s\n" % enrollment)
        signed = click.prompt("File containing signed statement", type=str, default=config.sig_enroll_filename)
        f = open(signed, 'r')
        sig = f.read()
        click.echo(validate_enrollment(sig))
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
