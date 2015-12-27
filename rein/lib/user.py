import click
import os
import json
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import config

Base = declarative_base()

class User(Base):
    __tablename__ = 'identity'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    contact = Column(String(250), nullable=False)
    maddr = Column(String(64), nullable=False)
    daddr = Column(String(64), nullable=False)

    def __init__(self, name, contact, maddr, daddr):
        self.name = name
        self.contact = contact
        self.maddr = maddr
        self.daddr = daddr

def create_account(engine, session):
    Base.metadata.create_all(engine)
    name = click.prompt("Enter name or handle", type=str)
    contact = click.prompt("Email or BitMessage address", type=str)
    maddr = click.prompt("Master Bitcoin address", type=str)
    daddr = click.prompt("Delegate Bitcoin address", type=str)
    new_identity = User(name, contact, maddr, daddr)
    session.add(new_identity)
    session.commit()
    data = {'name': name, 'contact': contact, 'maddr': maddr, 'daddr': daddr}
    if not os.path.isfile(config.backup_filename):
        f = open(config.backup_filename,'w')
        try:
            f.write(json.dumps(data))
            click.echo("Backup saved successfully to %s" % config.backup_filename)
        except:
            raise RuntimeError('Problem writing user details to json backup file.')
        f.close()
    else:
        click.echo("Backup file already exists. Please run with --backup to save "\
                   "user details to file.")
    return new_identity

def import_account(engine, session):
    Base.metadata.create_all(engine)
    backup_filename = click.prompt("Enter backup file name", type=str, default=config.backup_filename)    
    f = open(backup_filename, 'r')
    try:
        data = json.loads(f.read())
    except:
        raise RuntimeError('Backup file %s not valid json.' % backup_filename)
    new_identity = User(data['name'], data['contact'], data['maddr'], data['daddr'])
    session.add(new_identity)
    session.commit()
    return new_identity
