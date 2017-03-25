import os
import sys
import json
import click
import getpass
from .bitcoinecdsa import privkey_to_address, pubkey, pubkey_to_address, sign
from .bitcoinaddress import check_bitcoin_address
from .validate import validate_enrollment
from .user import User, Base
from .util import unique
from .document import Document
from .bitcoinaddress import generate_sin
from .rating import get_average_user_rating_display
import rein.lib.crypto.bip32 as bip32


def shorten(text, length=60):
    if length - 3 < len(text) < length:
        return text[0:length-1]
    elif len(text) > length - 3:
        return text[0:length-1] + '...'
    else:
        return text


def short_addr(text):
    return text[0:10] + '...' + text[-8:]


def highlight(string, status, bold):
    attr = []
    if status:
        # green
        attr.append('32')
    else:
        # red
        attr.append('31')
    if bold:
        attr.append('1')
    return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)


def job_link(j):
    return '<a href="/job/%s">%s</a>' % (j['Job ID'], j['Job name'])


def get_choice(choices, name):
    choice = -1
    while(choice >= len(choices) or choice < 0) and choice != 'q':
        choice = click.prompt('Choose a '+name+' (q to quit)', type=str)
        try:
            choice = int(choice)
        except:
            choice = choice
    return choice


# def btc_addr_prompt(name):
#     title = hilight(name.capitalize() + " Bitcoin address", True, True)
#     addr = click.prompt(title, type=str)
#     while not check_bitcoin_address(addr.strip()):
#         addr = click.prompt("Invalid.\n" + title, type=str)
#     return addr


# def btc_privkey_prompt(name, addr=None):
#     title = hilight(name.capitalize() + " Bitcoin private key: ", True, True)
#     privkey = getpass.getpass(title)
#     if addr:
#         while privkey_to_address(privkey.strip()) != addr:
#             privkey = getpass.getpass("Not valid or corresponding to target address.\n" + title)
#     else:
#         while not privkey_to_address(privkey.strip()):
#             privkey = getpass.getpass("Invalid private key.\n" + title)
#     return privkey.strip()


def identity_prompt(rein):
    users = rein.session.query(User).filter(User.enrolled == True,
                                            User.testnet == rein.testnet).all()
    user_count = len(users) 
    index = 0
    i = 0
    for user in users:
        click.echo('%s - %s' % (str(index + 1), user.name))
        index += 1
    while i > user_count or i < 1:
        i = click.prompt('Please choose an identity', type=int)
    rein.user = rein.session.query(User).filter(User.name == users[i - 1].name).first()
    return rein.user


# ---- Account creation and import ----

def create_account(rein):
    Base.metadata.create_all(rein.engine)

    # ---- Contact data ----

    name = click.prompt(highlight("\nEnter name or handle", True, True), type=str)
    contact = click.prompt(highlight("Email or BitMessage address", True, True), type=str)

    # ---- Mnemonic ----

    click.echo(highlight('\nHere is your 12 word mnemonic. Keep it secure - it is the key to\n'
               'accessing your Rein account, and is only showed once.\n', True, True))
    mnemonic = bip32.generate_mnemonic(128)
    click.echo(' '.join(mnemonic))
    confirm_mnemonic = click.confirm(highlight('\nConfirm that you put down the mnemonic.\n', True, True),
                                     default=False)
    if confirm_mnemonic:
        click.echo(highlight('\nGenerating BIP32 data...\n', True, True))
        # TODO - Transform it into a class with all the properties
        key = bip32.mnemonic_to_key(mnemonic)
        mprv = bip32.get_master_private_key(key)
        maddr = bip32.get_master_address(key)
        daddr = bip32.get_delegate_address(key)
        dkey = bip32.get_delegate_private_key(key)
        dxprv = bip32.get_delegate_extended_key(key)
        msin = generate_sin(maddr)
    else:
        click.echo(highlight('\nTo sign up for Rein you have to put down the mnemonic. Aborting.', False, True))
        quit()

    # ---- Mediator ----

    will_mediate = click.confirm(highlight('Are you willing to mediate?', True, True), default=False)
    mediator_fee = 1
    if will_mediate:
        mediator_fee = click.prompt(highlight("Mediator fee (%)", True, True), default=1.0)

    # ---- Registering user ----

    user_data = {'name': name,
                 'contact': contact,
                 'maddr': maddr,
                 'daddr': daddr,
                 'dkey': dkey,
                 'dxprv': dxprv,
                 'will_mediate': will_mediate,
                 'mediator_fee': mediator_fee,
                 'msin': msin,
                 'testnet': rein.testnet}
    new_identity = User(user_data)
    rein.session.add(new_identity)
    rein.session.commit()

    # ---- Signing enrollment document ----
    # No signature verification necessary as enrollment is signed by a Rein-generated key.

    rein.user = new_identity
    enrollment = build_enrollment_from_dict(user_data)
    signature = sign(mprv,json.dumps(enrollment,sort_keys=True))
    signed_enrollment = enrollment
    signed_enrollment['signature'] = signature
    signed_enrollment['signature_address'] = maddr
    User.set_enrolled(rein, new_identity)
    document = Document(rein, 'enrollment', json.dumps(signed_enrollment,sort_keys=True), sig_verified=True, testnet=rein.testnet)
    rein.session.add(document)
    rein.session.commit()

    # ---- Writing to backup file ----
    if not os.path.isfile(rein.backup_filename):
        f = open(rein.backup_filename, 'w')
        try:
            f.write(json.dumps(user_data))
            click.echo("Backup saved successfully to %s" % rein.backup_filename)
        except:
            raise RuntimeError('Problem writing user details to json backup file.')
        f.close()
    else:
        click.echo("Backup file already exists. Please run with --backup to save "
                   "user details to file.")
    return rein.user


def build_enrollment_from_dict(user_data):
    enrollment = {}
    enrollment['Title'] = 'Rein User Enrollment'
    enrollment['User'] = user_data['name']
    enrollment['Contact'] = user_data['contact']
    enrollment['Master signing address'] = user_data['maddr']
    enrollment['Secure Identity Number'] = user_data['msin']
    enrollment['Delegate signing address'] = user_data['daddr']
    if user_data['will_mediate']:
        enrollment['Willing to mediate'] = 'True'
        enrollment['Mediator public key'] = pubkey(user_data['dkey'])
        enrollment['Mediator fee'] = user_data['mediator_fee']
    else:
        enrollment['Willing to mediate'] = 'False'
    if user_data['testnet']:
        enrollment['Testnet'] = 'True'    
    return enrollment

def import_account(rein, mprv=None, mnemonic=None):
    Base.metadata.create_all(rein.engine)
    backup_filename = click.prompt("Enter backup file name", type=str, default=rein.backup_filename)
    f = open(backup_filename, 'r')
    try:
        user_data = json.loads(f.read())
    except:
        raise RuntimeError('Backup file %s not valid json.' % backup_filename)
    if not check_bitcoin_address(user_data['maddr']) or not check_bitcoin_address(user_data['daddr']):
        click.echo("Invalid Bitcoin address(es) in backup file.")
        sys.exit()
    if 'testnet' not in user_data:
        click.echo("Warning: testnet not set in backup. Setting to " + str(rein.testnet))
        user_data['testnet'] = rein.testnet
    if 'dxprv' not in user_data:
        user_data['dxprv'] = None

    new_identity = User(user_data)
    rein.session.add(new_identity)
    rein.session.commit()
    rein.user = new_identity

    # ---- Signing enrollment ----

    if mnemonic:
        key = bip32.mnemonic_to_key(mnemonic)
        mprv = bip32.get_master_private_key(key)
    elif mprv:
        if not privkey_to_address(mprv):
            raise Exception('Invalid master private key.')


    enrollment = build_enrollment_from_dict(user_data)
    signature = sign(mprv,json.dumps(enrollment,sort_keys=True))
    signed_enrollment = enrollment
    signed_enrollment['signature'] = signature
    signed_enrollment['signature_address'] = user_data['maddr']

    User.set_enrolled(rein, new_identity)
    document = Document(rein, 'enrollment', json.dumps(signed_enrollment,sort_keys=True), sig_verified=True, testnet=rein.testnet)
    rein.session.add(document)
    rein.session.commit()
    return rein.user

def build_enrollment(rein):

    enrollment = {}
    user = rein.user
    enrollment['Title'] = 'Rein User Enrollment'
    enrollment['User'] = user.name
    enrollment['Contact'] = user.contact
    enrollment['Master signing address'] = user.maddr
    enrollment['Delegate signing address'] = user.daddr
    if user.will_mediate:
        enrollment['Willing to mediate'] = 'True'
        enrollment['Mediator public key'] = pubkey(user.dkey)
        enrollment['Mediator fee'] = user.mediator_fee
    else:
        enrollment['Willing to mediate'] = 'False'
    if rein.testnet:
        enrollment['Testnet'] = 'True'
    return enrollment

def enroll(rein):
    user = rein.user
    Base.metadata.create_all(rein.engine)
    enrollment = build_enrollment(rein)
    f = open(rein.enroll_filename, 'w')
    f.write(json.dumps(enrollment,sort_keys=True))
    f.close()
    click.echo("%s\n" % enrollment)
    done = False
    while not done:
        filename = click.prompt(highlight("File containing signed statement", True, True), type=str, default=rein.sig_enroll_filename)
        if os.path.isfile(filename):
            done = True
        else:
            click.echo("File not found. Please check the file name and location and try again.")
    f = open(filename, 'r')
    signed = f.read()
    res = validate_enrollment(signed)
    if res:
        User.set_enrolled(rein, user)
        # insert signed document into documents table as type 'enrollment'
        document = Document(rein, 'enrollment', signed, sig_verified=True, testnet=rein.testnet)
        rein.session.add(document)
        rein.session.commit()
    return res


# ---- Jobs | Mediators | Workers ----

def mediator_prompt(log, url, user, rein, eligible_mediators):
    mediators = unique(eligible_mediators, 'Mediator public key')
    key = pubkey(rein.user.dkey)
    i = 0
    for m in mediators:
        if m["Mediator public key"] == key:
            mediators.remove(m)
            continue

        click.echo('{} - {} - {} - Fee: {} - Public key: {}'.format(
            str(i), 
            m['User'],
            get_average_user_rating_display(log, url, user, rein, m['Secure Identity Number'], True),
            m['Mediator fee'], 
            m['Mediator public key']
            )
        )
        i += 1
    if len(mediators) == 0:
        click.echo("None found.")
        return None
    choice = get_choice(mediators, 'mediator')
    if choice == 'q':
        return False
    return mediators[choice]


# called in offer()
def bid_prompt(log, url, user, rein, bids):
    """
    Prompts user to choose a bid on one of their jobs. This means they should be the job creator and
    not the worker or mediator.
    """
    i = 0
    valid_bids = []
    key = pubkey(rein.user.dkey)
    for b in bids:
        if 'Description' not in b or b['Job creator public key'] != key:
            continue 

        worker_msin = generate_sin(b['Worker master address'])
        click.echo('{} - {} - {} - {} - {} - {} bitcoin'.format(
            str(i), 
            b['Job name'], 
            b["Worker"],
            get_average_user_rating_display(log, url, user, rein, worker_msin, True),
            shorten(b['Description']), 
            b['Bid amount (BTC)']
            )
        )
        valid_bids.append(b)
        i += 1
    if len(valid_bids) == 0:
        click.echo('No bids available.')
        return None
    choice = get_choice(valid_bids, 'bid')
    if choice == 'q':
        click.echo('None chosen.')
        return False
    bid = valid_bids[choice]
    click.echo('You have chosen %s\'s bid.\n\nFull description: %s\nBid amount (BTC): %s\n\nPlease review carefully before accepting. (Ctrl-c to abort)' % 
               (bid['Worker'], bid['Description'], bid['Bid amount (BTC)']))
    return bid


def job_prompt(log, url, user, rein, jobs):
    """
    Prompt user for jobs they can bid on. Filters out jobs they created or are mediator for.
    """
    key = pubkey(rein.user.dkey)
    valid_jobs = []
    for j in jobs:
        if j['Job creator public key'] != key and j['Mediator public key'] != key:
            valid_jobs.append(j)
    if len(valid_jobs) == 0:
        click.echo('None found.')
        return None

    i = 0
    for j in valid_jobs:
        creator_msin = generate_sin(j['Job creator master address'])
        click.echo('{} - {} - {} - {} - {}'.format(
            str(i), 
            j["Job creator"], 
            get_average_user_rating_display(log, url, user, rein, creator_msin, True),
            j['Job name'], 
            shorten(j['Description'])
            )
        )
        i += 1
    choice = get_choice(valid_jobs, 'job')
    if choice == 'q':
        return False
    job = valid_jobs[choice]
    click.echo('You have chosen a Job posted by %s.\n\nFull description: %s\n\nPlease pay attention '
               'to each requirement and provide a time frame to complete the job. (Ctrl-c to abort)\n' % 
               (job['Job creator'], job['Description']))
    return job


def delivery_prompt(rein, choices, detail='Description'):
    choices = unique(choices, 'Job ID')
    i = 0
    for c in choices:
        if 'Bid amount (BTC)' not in c:
            continue
        if detail in c:
            click.echo('%s - %s - %s BTC - %s' % (str(i), c['Job name'], c['Bid amount (BTC)'], shorten(c[detail])))
        else:
            click.echo('%s - %s - %s BTC - %s' % (str(i), c['Job name'], c['Bid amount (BTC)'], shorten(c['Description'])))
        i += 1
    choice = get_choice(choices, 'job')
    if choice == 'q':
        return None
    chosen = choices[choice]
    click.echo('You have chosen to post deliverables. The following is from your winning bid.'
               '\n\nDescription: %s\n\nPlease review carefully before posting deliverables. '
               'This will be public and reviewed by mediators if disputed. (Ctrl-c to abort)\n' % 
               (chosen['Description'],))
    return chosen


def accept_prompt(rein, choices, detail='Description'):
    i = 0
    click.echo("Offers and Deliveries")
    click.echo("---------------------")
    for c in choices:
        if 'Primary escrow redeem script' not in c:
            continue
        if detail in c:
            click.echo('%s: %s - %s - %s - %s' % (c['state'].title(), str(i),
                        c['Job name'], c['Job ID'], shorten(c[detail])))
        else:
            click.echo('%s: %s - %s - %s - %s' % (c['state'].title(), str(i),
                        c['Job name'], c['Job ID'], shorten(c['Description'])))
        i += 1
    choice = get_choice(choices, 'delivery or offer')
    if choice == 'q':
        return None
    chosen = choices[choice]
    if detail in chosen:
        contents = chosen[detail]
    else:
        contents = chosen['Description']
    click.echo('You have chosen to accept the following deliverables. \n\n%s: %s\nAccepted Bid amount (BTC): %s\n'
               'Primary escrow redeem script: %s\n'
               'Worker address: %s\n\n'
               'Mediator escrow redeem script: %s\n'
               'Mediator address: %s\n'
               '\nPlease review carefully before accepting. Once you upload your signed statement, the mediator should no '
               'longer provide a refund. (Ctrl-c to abort)\n' % 
               (detail,
                contents, chosen['Bid amount (BTC)'],
                chosen['Primary escrow redeem script'],
                pubkey_to_address(chosen['Worker public key']),
                chosen['Mediator escrow redeem script'],
                pubkey_to_address(chosen['Mediator public key'])
               )
              )
    return chosen

def acceptresolution_prompt(rein, choices, detail='Description'):
    i = 0
    click.echo("Resolutions")
    click.echo("---------------------")
    for c in choices:
        if 'Primary escrow redeem script' not in c:
            continue
        if detail in c:
            click.echo('%s: %s - %s - %s - %s - %s' % ("Resolution", str(i),
                        c['Job name'], c['Job ID'], shorten(c[detail]),'Client gets '+c['Primary client payment amount']))
        i += 1
    choice = get_choice(choices, 'resolution')
    if choice == 'q':
        return None
    chosen = choices[choice]
    if detail in chosen:
        contents = chosen[detail]
    else:
        contents = chosen['Description']
    click.echo('You have chosen to accept the following resolution. \n\n%s: %s\n'
               'Primary escrow redeem script: %s\n'
               'Worker address: %s\n\n'
               'Mediator escrow redeem script: %s\n'
               'Mediator address: %s\n'
               'Client payment amount: %s\n'
               '\nPlease review carefully before accepting. Once you upload your signed statement, the mediator should no '
               'longer provide a refund. (Ctrl-c to abort)\n' % 
               (detail,
                contents,
                chosen['Primary escrow redeem script'],
                pubkey_to_address(chosen['Worker public key']),
                chosen['Mediator escrow redeem script'],
                pubkey_to_address(chosen['Mediator public key']),
                chosen['Primary client payment amount']
               )
              )
    return chosen

    

def dispute_prompt(rein, choices, detail='Description'):
    i = 0
    for c in choices:
        if 'Primary escrow redeem script' not in c:
            continue
        if detail in c:
            click.echo('%s - %s - %s - %s' % (str(i), c['Job name'], c['Job ID'], shorten(c[detail])))
        else:
            click.echo('%s - %s - %s - %s' % (str(i), c['Job name'], c['Job ID'], shorten(c['Description'])))
        i += 1
    choice = get_choice(choices, 'job')
    if choice == 'q':
        return None
    chosen = choices[choice]
    if detail in chosen:
        contents = chosen[detail]
    else:
        contents = chosen['Description']
    click.echo('You have chosen to dispute the following deliverables. \n\n%s: %s\n\nPlease provide as much detail as possible. '
               'For the primary payment, you should build and sign one that refunds you at %s. (Ctrl-c to abort)\n' % 
               (detail, contents, rein.user.daddr))
    return chosen


def resolve_prompt(rein, choices, detail='Dispute detail'):
    i = 0
    for c in choices:
        if 'Primary escrow redeem script' not in c:
            continue
        click.echo('%s - %s - %s - %s' % (str(i), c['Job name'], c['Job ID'], shorten(c[detail])))
        i += 1
    choice = get_choice(choices, 'dispute')
    if choice == 'q':
        return None
    chosen = choices[choice]
    click.echo('You have chosen to resolve this dispute. \n\n%s: %s\n\n'
               'For the mediator payment, you should build and sign one that pays you at %s. (Ctrl-c to abort)\n' %
               (detail, chosen[detail], rein.user.daddr))
    return chosen
