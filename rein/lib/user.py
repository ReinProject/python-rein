import click
import os
import sys
import json
import getpass
from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from bitcoinaddress import check_bitcoin_address
from bitcoinecdsa import privkey_to_address
#import config

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
    title = name.capitalize() + " Bitcoin private key: "
    privkey = getpass.getpass(title)
    if addr:
        while privkey_to_address(privkey) != addr:
            privkey = getpass.getpass("Doesn't match target address.\n" + title)
    else:
        click.echo(privkey)
        click.echo(privkey_to_address(privkey))
        while not privkey_to_address(privkey):
            privkey = getpass.getpass("Invalid private key.\n" + title)
    return privkey


def create_account(rein):
    Base.metadata.create_all(rein.engine)
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
    rein.session.add(new_identity)
    rein.session.commit()
    data = {'name': name,
            'contact': contact,
            'maddr': maddr,
            'daddr': daddr,
            'dkey': dkey,
            'will_mediate': will_mediate,
            'mediation_fee': mediation_fee}
    if not os.path.isfile(rein.backup_filename):
        f = open(rein.backup_filename, 'w')
        try:
            f.write(json.dumps(data))
            click.echo("Backup saved successfully to %s" % rein.backup_filename)
        except:
            raise RuntimeError('Problem writing user details to json backup file.')
        f.close()
    else:
        click.echo("Backup file already exists. Please run with --backup to save "
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


def select_identity(session):
    names = ['Alice', 'Bob', 'Charlie', 'Dan']
    user_count = session.query(User).count()
    index = 1
    for name in names[0:user_count]:
        click.echo('%s - %s' % (str(index), name))
        index += 1
    i = click.prompt('Please choose an identity', type=int)
    while i > user_count or i < 1:
        i = click.prompt('Please choose an identity', type=int)
    return session.query(User).filter(User.name == names[i - 1]).first()


def get_user(session, multi, identity):
    if multi and identity:
        user = session.query(User).filter(User.name == identity).first()
    elif multi:
        user = select_identity(session)
    else:
        user = session.query(User).first()
    return user
