import click
import os
import sys 
import json
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from bitcoinaddress import check_bitcoin_address
from bitcoinecdsa import privkey_to_address
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
    will_mediate = Column(Boolean, nullable=False)
    mediation_fee = Column(Float, nullable=False)

    def __init__(self, name, contact, maddr, daddr, dkey, will_mediate, mediation_fee):
        self.name = name
        self.contact = contact
        self.maddr = maddr
        self.daddr = daddr
        self.dkey = dkey
        self.will_mediate = will_mediate
        self.mediation_fee = mediation_fee

def btc_addr_prompt(name):
    title = name.capitalize() + " Bitcoin address"
    addr = click.prompt(title, type=str)
    while not check_bitcoin_address(addr):
        addr = click.prompt("Invalid.\n" + title, type=str)
    return addr

def btc_privkey_prompt(name, addr=None):
    title = name.capitalize()+" Bitcoin private key: "
    privkey = getpass.getpass(title)
    if addr:
        while privkey_to_address(privkey) != addr:
            privkey = getpass.getpass("Doesn't match target address.\n"+title)
    else:
        while not privkey_to_address(privkey):
            privkey = getpass.getpass("Invalid private key.\n"+title)
    return privkey

def create_account(engine, session):
    Base.metadata.create_all(engine)
    name = click.prompt("Enter name or handle", type=str)
    contact = click.prompt("Email or BitMessage address", type=str)
    maddr = btc_addr_prompt("Master")
    daddr = btc_addr_prompt("Delegate")
    dkey = btc_privkey_prompt("Delegate")
    will_mediate = click.confirm("Willing to mediate:", default=False)
    mediation_fee = 1
    if will_mediate:
        mediation_fee = click.prompt("Mediation fee (%)", default=1)
    new_identity = User(name, contact, maddr, daddr, dkey, will_mediate, mediation_fee)
    session.add(new_identity)
    session.commit()
    data = {'name': name, 
            'contact': contact, 
            'maddr': maddr, 
            'daddr': daddr, 
            'dkey': dkey,
            'will_mediate': will_mediate,
            'mediation_fee': mediation_fee}
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
    new_identity = User(data['name'], 
                        data['contact'], 
                        data['maddr'], 
                        data['daddr'], 
                        data['dkey'], 
                        data['will_mediate'], 
                        data['mediation_fee'])
    session.add(new_identity)
    session.commit()
    return new_identity
