import os
import sys
import json
import click
import getpass
from bitcoinecdsa import privkey_to_address, pubkey
from bitcoinaddress import check_bitcoin_address
from validate import validate_enrollment
from user import User, Base
from document import Document


def shorten(text, length=60):
    if len(text) > length - 3 and len(text) < length:
        return text[0:length-1]
    elif len(text) > length - 3:
        return text[0:length-1] + '...'
    else:
        return text
        

def get_choice(choices, name):
    choice = -1
    while(choice >= len(choices) or choice < 0) and choice != 'q':
        choice = click.prompt('Choose a '+name+' (q to quit)', type=str)
        try:
            choice = int(choice)
        except:
            choice = choice
    return choice


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
            privkey = getpass.getpass("Not valid or corresponding to target address.\n" + title)
    else:
        while not privkey_to_address(privkey):
            privkey = getpass.getpass("Invalid private key.\n" + title)
    return privkey


def identity_prompt(rein):
    names = ['Alice', 'Bob', 'Charlie', 'Dan']
    user_count = rein.session.query(User).count()
    index = 0
    i = 0
    for name in names[0:user_count]:
        click.echo('%s - %s' % (str(index + 1), name))
        index += 1
    while i > user_count or i < 1:
        i = click.prompt('Please choose an identity', type=int)
    rein.user = rein.session.query(User).filter(User.name == names[i - 1]).first()
    return rein.user


def create_account(rein):
    Base.metadata.create_all(rein.engine)
    name = click.prompt("Enter name or handle", type=str)
    contact = click.prompt("Email or BitMessage address", type=str)
    maddr = btc_addr_prompt("Master")
    daddr = btc_addr_prompt("Delegate")
    dkey = btc_privkey_prompt("Delegate", daddr)
    will_mediate = click.confirm("Willing to mediate:", default=False)
    mediation_fee = 1
    if will_mediate:
        mediation_fee = click.prompt("Mediation fee (%)", default=1.0)
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
    rein.user = new_identity
    return rein.user


def import_account(rein):
    Base.metadata.create_all(rein.engine)
    backup_filename = click.prompt("Enter backup file name", type=str, default=rein.backup_filename)
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
    rein.session.add(new_identity)
    rein.session.commit()
    rein.user = new_identity
    return rein.user


def enroll(rein):
    Base.metadata.create_all(rein.engine)
    user = rein.user
    mediator_extras = ''
    if user.will_mediate:
        mediator_extras = "\nMediator pubkey: %s\nMediation fee: %s%%" % \
                          (pubkey(user.dkey), user.mediation_fee)
    enrollment = "Rein User Enrollment\nUser: %s\nContact: %s\nMaster signing address: %s" \
                 "\nDelegate signing address: %s\nWilling to mediate: %s%s" % \
                 (user.name, user.contact, user.maddr, user.daddr, user.will_mediate, mediator_extras)
    f = open(rein.enroll_filename, 'w')
    f.write(enrollment)
    f.close()
    click.echo("\n%s\n" % enrollment)
    done = False
    while not done:
        filename = click.prompt("File containing signed statement", type=str, default=rein.sig_enroll_filename)
        if os.path.isfile(filename):
            done = True
    f = open(filename, 'r')
    signed = f.read()
    res = validate_enrollment(signed)
    if res:
        # insert signed document into documents table as type 'enrollment'
        document = Document(rein, 'enrollment', signed, sig_verified=True)
        rein.session.add(document)
        rein.session.commit()
    return res
