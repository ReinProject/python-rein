import json
import re
import os.path
import time
import click
import sqlite3
from subprocess import check_output

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.user import User, Base
 

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
@click.command()
def main():
    '''Rein CLI'''
    click.echo("\nWelcome to Rein, the decentralized services marketplace.\n")
    if not os.path.isfile(db_filename):
        click.echo("It looks like this is your first time running Rein.\nDo you want to import a backup or create a new account?\n1 - Import\n2 - Create\n")
        choice = 0
        while choice not in (1, 2):

            choice = click.prompt("Choice", type=int, default=2)
            if choice == 2:
                Base.metadata.create_all(engine)
                name = click.prompt("Enter name or handle", type=str)
                contact = click.prompt("Enter email or BitMessage address", type=str)

                new_identity = User(name, contact)
                session.add(new_identity)
                session.commit()

                data = {'name': name, 'contact': contact}
                backup_filename = 'rein-backup.json'
                if not os.path.isfile(backup_filename):
                    f = open(backup_filename,'w')
                    try:
                        f.write(json.dumps(data))
                        click.echo("Backup saved successfully to %s" % backup_filename)
                    except:
                        raise RuntimeError('Problem writing user details to json backup file.')
                    f.close()
                else:
                    click.echo("Backup flie already exists. Please run with --backup to save user details to file.")
#u = User(name, email)
            elif choice == 1:
                Base.metadata.create_all(engine)
                backup_filename = click.prompt("Enter backup file name: (rein-backup.json)", type=str, default='rein-backup.json')    
                f = open(backup_filename, 'r')
                try:
                    data = json.loads(f.read())
                except:
                    raise RuntimeError('Backup file %s not valid json.' % backup_filename)

                new_identity = User(data['name'], data['contact'])
                session.add(new_identity)
                session.commit()
                
