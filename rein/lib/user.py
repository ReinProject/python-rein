import click
import os
import sys 
import json
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from bitcoinaddress import check_bitcoin_address
from pybitcointools import privkey_to_address
import config

Base = declarative_base()

class User(Base):
    __tablename__ = 'identity'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    contact = Column(String(250), nullable=False)
    maddr = Column(String(64), nullable=False)
    daddr = Column(String(64), nullable=False)
    dkey = Column(String(64), nullable=False)

    def __init__(self, name, contact, maddr, daddr, dkey):
        self.name = name
        self.contact = contact
        self.maddr = maddr
        self.daddr = daddr
        self.dkey = dkey

def create_account(engine, session):
    Base.metadata.create_all(engine)
    name = click.prompt("Enter name or handle", type=str)
    contact = click.prompt("Email or BitMessage address", type=str)
    maddr = click.prompt("Master Bitcoin address", type=str)
    while not check_bitcoin_address(maddr):
        maddr = click.prompt("Invalid.\nMaster Bitcoin address", type=str)
    daddr = click.prompt("Delegate Bitcoin address", type=str)
    while not check_bitcoin_address(daddr):
        daddr = click.prompt("Invalid.\nDelegate Bitcoin address", type=str)
    dkey = click.prompt("Delegate Bitcoin addres private key", type=str)
    while privkey_to_address(dkey) != daddr:
        dkey = click.prompt("Invalid or doesn't match address.\nDelegate Bitcoin address private key", type=str)
    new_identity = User(name, contact, maddr, daddr, dkey)
    session.add(new_identity)
    session.commit()
    data = {'name': name, 'contact': contact, 'maddr': maddr, 'daddr': daddr, 'dkey': dkey}
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
    if not check_bitcoin_address(data['maddr']) or not check_bitcoin_address(data['daddr']):
        click.echo("Invalid Bitcoin address(es) in backup file.")
        sys.exit()
    new_identity = User(data['name'], data['contact'], data['maddr'], data['daddr'], data['dkey'])
    session.add(new_identity)
    session.commit()
    return new_identity
