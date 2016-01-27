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
    click.echo('\nIn Rein, all of your activity is linked to your Master Bitcoin\n'
               'address. This includes everything from setting your contact info\n'
               'and creating a job, to getting paid.\n\n'
               'You should keep the private key that corresponds to this address\n'
               'offline the vast majority of the time. It will only be used to\n'
               'create or update your main user record.\n')
    maddr = btc_addr_prompt('Master')

    click.echo('\nInstead of the Master address, python-rein uses another address that has\n'
               'been authorized for day-to-day activities. This delegate\n'
               'address\' private key will be stored locally and used by\n'
               'python-rein to authenticate documents and access on your behalf.\n\n'
               'If this computer or the delegate private key are lost or stolen,\n'
               'you will use your Master private key to revoke the delegate\n'
               'address and grant authority to a new address.\n')
    daddr = btc_addr_prompt('Delegate')
    click.echo('In order for python-rein to authenticate on your behalf, it\n'
               'will store the delegate\'s private key in the local database.\n')
    dkey = btc_privkey_prompt('Delegate', daddr)
    click.echo('\nRein requires three parties to every service transaction. The\n'
               'job creator, mediator and worker. Mediators are called upon to\n'
               'resolve disputes and may use their delegate key to do so.\n\n'
               'In exchange, mediators may charge a fee. Funds to pay the\n'
               'mediator\'s fee are placed in an address that ensures those\n'
               'funds will go only to the mediator.\n')
    will_mediate = click.confirm('Are you willing to mediate?', default=False)
    mediator_fee = 1
    if will_mediate:
        mediator_fee = click.prompt("Mediator fee (%)", default=1.0)
    new_identity = User(name, contact, maddr, daddr, dkey, will_mediate, mediator_fee)
    rein.session.add(new_identity)
    rein.session.commit()
    data = {'name': name,
            'contact': contact,
            'maddr': maddr,
            'daddr': daddr,
            'dkey': dkey,
            'will_mediate': will_mediate,
            'mediator_fee': mediator_fee}
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
                        data['mediator_fee'])
    rein.session.add(new_identity)
    rein.session.commit()
    rein.user = new_identity
    return rein.user


def enroll(rein):
    Base.metadata.create_all(rein.engine)
    user = rein.user
    mediator_extras = ''
    if user.will_mediate:
        mediator_extras = "\nMediator public key: %s\nMediator fee: %s%%" % \
                          (pubkey(user.dkey), user.mediator_fee)
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
