import sys
import json
import re
import random
import string
import requests
import hashlib
import click
import time
import os
import traceback
from pprint import pprint
from datetime import datetime
from sqlalchemy import and_


config_dir = os.path.join(os.path.expanduser('~'), '.rein')
if not os.path.isdir(config_dir):
    os.mkdir(config_dir)

# Import helper functions
from .lib.ui import *
from .lib.validate import filter_and_parse_valid_sigs, parse_document, choose_best_block, filter_out_expired, remote_query
from .lib.bitcoinecdsa import sign, pubkey
from .lib.market import * 
from .lib.util import unique
from .lib.io import safe_get
from .lib.script import build_2_of_3, build_mandatory_multisig, check_redeem_scripts
from .lib.localization import init_localization
from .lib.transaction import partial_spend_p2sh, spend_p2sh, spend_p2sh_mediator, partial_spend_p2sh_mediator, partial_spend_p2sh_mediator_2
from .lib.rating import add_rating, get_user_jobs, get_average_user_rating, get_averave_user_rating_display

# Import config
import rein.lib.config as config

# Create tables
import rein.lib.models

# Import models
from .lib.persistconfig import PersistConfig
from .lib.user import User
from .lib.bucket import Bucket
from .lib.document import Document
from .lib.placement import Placement
from .lib.order import Order, STATE
from .lib.mediator import Mediator

rein = config.Config()
init_localization()

import bitcoin
from bitcoin.wallet import P2PKHBitcoinAddress
from bitcoin.core import x
if (rein.testnet): bitcoin.SelectParams('testnet')
init_localization()


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):
    _("""
    Rein is a decentralized professional services market and Python-rein is a client
that provides a user interface. Use this program from your local browser or command 
line to create an account, post a job, bid, etc.

\b
    Quick start:
        $ rein start     - create an identity, run the Web UI
        $ rein buy       - request microhosting
        $ rein sync      - push your identity to microhosting servers
        $ rein status    - get user status, or dump of job's documents

\b
    Workers
        $ rein bid       - view and bid on jobs
        $ rein deliver   - complete job by providing deliverables

\b
    Disputes
        $ rein workerdispute    - worker files dispute
        $ rein creatordispute   - job creator files dispute
        $ rein resolve          - mediator posts decision

    For more info and the setup guide visit: http://reinproject.org
    """)
    if debug:
        click.echo("Debuggin'")
    pass


@cli.command()
@click.option('--multi/--no-multi', default=False, help="add even if an identity exists")
def setup(multi):
    _("""
    Setup or import an identity.

    You will choose a name or handle for your account, include public contact information, 
    and a delegate Bitcoin address/private key that the program will use to sign documents
    on your behalf. An enrollment document will be created and you will need to sign it
    with your master Bitcoin private key.
    """)
    log = rein.get_log()
    if multi:
        rein.set_multiuser()
    log.info('entering setup')
    if multi or rein.has_no_account():
        click.echo("\n" + highlight(_("Welcome to Rein."), True, True) + "\n\n" +
                   _("Do you want to import a backup or create a new account?\n\n") +
                   _("1 - Create new account\n2 - Import backup\n"))
        choice = click.prompt(highlight("Choice", True, True), type=int, default=1)

        if choice == 1:
            create_account(rein)
            log.info('account created')
        elif choice == 2:
            # If a delegate xprv is in the backup, means userr signed up with the new mnemonic version
            click.echo("\nDoes your backup include the delegate extended private key (starts with xprv)?\n"
                       "If you don't specify this correctly Rein will fail to sign your enrollment\n\n"
                       "1 - Yes\n2 - No\n")
            version = click.prompt(highlight("Choice", True, True), type=int, default=2)
            if version == 1:
                import_account(rein, mnemonic=click.prompt(highlight("Enter the 12-word mnemonic Rein showed you at signup:", True, True)))
            elif version == 2:
                import_account(rein, mprv=click.prompt(highlight("Enter the master private key you used to sign your enrollment message with:", True, True)))
            log.info('account imported')
        else:
            click.echo('Invalid choice')
            return
        click.echo("Enrollment complete. Run 'rein buy' to purchase microhosting (required for sync).")
        log.info('enrollment complete')
    else:
        click.echo("Identity already setup.")
    log.info('exiting setup')


@cli.command()
@click.option('--multi/--no-multi', '-m', default=False, help="prompt for identity to use")
@click.option('--identity', '-i', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.option('--defaults', '-d', default=None, help='file with form values')
@click.option('--dry-run/--no-dry-run', '-n', default=False, help='generate but do not store document')
def post(multi, identity, defaults, dry_run):
    """
    Post a job.
    """
    (log, user, key, urls) = init(multi, identity)
    form = {}
    if defaults:
        form = parse_document(open(defaults).read())
        if 'Title' in form and form['Title'] != 'Rein Job':
            return click.echo("Input file type: " + form['Title'])

    store = False if dry_run else True

    eligible_mediators = []
    blocks = []
    for url in urls:
        sel_url = "{0}query?owner={1}&query=mediators&testnet={2}"
        data = safe_get(log, sel_url.format(url, user.maddr, rein.testnet))
        if len(data['mediators']) == 0:
            click.echo('None found')
        if data['block_info']:
            blocks.append(data['block_info'])
        eligible_mediators += filter_and_parse_valid_sigs(rein, data['mediators'], 'Secure Identity Number')
    (block_hash, block_time) = choose_best_block(blocks)
    if block_hash is None:
        click.echo("None of your servers responded with block info.")
        return

    if 'Mediator public key' in form.keys():
        mediator = select_by_form(eligible_mediators, 'Mediator public key', form)
    else:
        click.echo("Post a job\n\nFunds for each job in Rein are stored in two multisig addresses. One address\n"
                   "is for the primary payment that will go to the worker on completion. The\n"
                   "second address pays the mediator to be available to resolve a dispute\n"
                   "if necessary. The second address should be funded according to the percentage\n"
                   "specified by the mediator and is in addition to the primary payment. The\n"
                   "listing below shows available mediators and the fee they charge. You should\n"
                   "consider the fee as well as any reputational data you are able to find when\n"
                   "choosing a mediator. Your choice may affect the number and quality of bids\n"
                   "you receive.\n")
        mediator = mediator_prompt(rein, eligible_mediators)
    if not mediator:
        return
    click.echo("Chosen mediator: " + str(mediator['User']))

    log.info('got user and key for post')
    job_guid = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(20))
    fields = [
                {'label': 'Job name',                       'not_null': form,
                    'help': 'Choose a brief but descriptive name for the job.'},
                {'label': 'Job ID',                         'value': job_guid},
                {'label': 'Tags', 'validator': is_tags, 'not_null': form,
                    'help': 'Each post can have a set of tags associated with it. Though not implemented yet,\n'
                            'these tags may be used in searches and filters later. No spaces, dashes, or\n'
                            'special characters are allowed. Please enter them as a comma-separated list.\n'
                            'Example: software, 3dprinting'},
                {'label': 'Description',                    'not_null': form},
                {'label': 'Block hash',                     'value': block_hash},
                {'label': 'Time',                           'value': str(block_time)},
                {'label': 'Expiration (days)',              'validator': is_int},
                {'label': 'Mediator',                       'value': mediator['User']},
                {'label': 'Mediator contact',               'value': mediator['Contact']},
                {'label': 'Mediator fee',                   'value': mediator['Mediator fee']},
                {'label': 'Mediator public key',            'value': mediator['Mediator public key']},
                {'label': 'Mediator master address',        'value': mediator['Master signing address']},
                {'label': 'Job creator',                    'value': user.name},
                {'label': 'Job creator contact',            'value': user.contact},
                {'label': 'Job creator public key',         'value': key},
                {'label': 'Job creator master address',     'value': user.maddr},
                {'label': 'Job creator delegate address',   'value': user.daddr},
             ]
    document_text = assemble_document('Job', fields)
    if not rein.testnet:
        m = re.search('test', document_text, re.IGNORECASE)
        if m:
            click.echo('Your post includes the word "test". If this post is a test, '
                       'please put rein into testnet mode with "rein testnet true" '
                       'and setup a test identity before posting.')
            if not click.confirm(highlight('Would you like to continue to post this on mainnet?', True, True), default=False):
                return

    document = sign_and_store_document(rein, 'job_posting', document_text, user.daddr, user.dkey, store)
    if document and store:
        click.echo("Posting created. Run 'rein sync' to push to available servers.")
    assemble_order(rein, document)
    log.info('posting signed') if document else log.error('posting failed')


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.option('--defaults', '-d', default=None, help='file with form values')
@click.option('--dry-run/--no-dry-run', '-n', default=False, help='generate but do not store document')
def bid(multi, identity, defaults, dry_run):
    """
    Bid on a job.

    Choose from available jobs posted to your registered servers, and create a bid.
    Your bid should include the price in bitcoin you're requesting to complete the
    job and when you expect to have it complete.
    """
    
    (log, user, key, urls) = init(multi, identity)
    form = {}
    if defaults:
        form = parse_document(open(defaults).read())
        if 'Title' in form and form['Title'] != 'Rein Bid':
            return click.echo("Input file type: " + form['Title'])
    store = False if dry_run else True

    jobs = []
    blocks = []
    for url in urls:    
        sel_url = "{0}query?owner={1}&query=jobs&testnet={2}"
        data = safe_get(log, sel_url.format(url, user.maddr, rein.testnet))
        if data['block_info']:
            blocks.append(data['block_info'])
        jobs += filter_and_parse_valid_sigs(rein, data['jobs'])
    (block_hash, block_time) = choose_best_block(blocks)

    live_jobs = filter_out_expired(rein, user, urls, jobs)
    unique_jobs = unique(live_jobs, 'Job ID')

    jobs = []
    for job in unique_jobs:
        order = Order.get_by_job_id(rein, job['Job ID'])
        if not order:
            order = Order(job['Job ID'], testnet=rein.testnet)
            rein.session.add(order)
            rein.session.commit()
        state = order.get_state(rein, Document)
        if state in ['job_posting', 'bid']:
            jobs.append(job)
    
    if len(jobs) == 0:
        click.echo('None found')
        return

    if 'Job ID' in form.keys():
        job = select_by_form(jobs, 'Job ID', form)
    else:
        job = job_prompt(rein, jobs)
    if not job:
        return

    log.info('got job for bid')
    primary_redeem_script, primary_addr = build_2_of_3([job['Job creator public key'],
                                                        job['Mediator public key'],
                                                        key])
    mediator_redeem_script, mediator_escrow_addr = build_mandatory_multisig(job['Mediator public key'],
                                                                            [job['Job creator public key'],key])
    fields = [
                {'label': 'Job name',                       'value_from': job},
                {'label': 'Worker',                         'value': user.name},
                {'label': 'Worker contact',                 'value': user.contact},
                {'label': 'Worker master address',          'value': user.maddr},
                {'label': 'Worker delegate address',        'value': user.daddr},
                {'label': 'Description',                    'not_null': form},
                {'label': 'Bid amount (BTC)',               'not_null': form},
                {'label': 'Primary escrow address',         'value': primary_addr},
                {'label': 'Mediator escrow address',        'value': mediator_escrow_addr},
                {'label': 'Job ID',                         'value_from': job},
                {'label': 'Job creator',                    'value_from': job},
                {'label': 'Job creator public key',         'value_from': job},
                {'label': 'Mediator public key',            'value_from': job},
                {'label': 'Worker public key',              'value': key},
                {'label': 'Primary escrow redeem script',   'value': primary_redeem_script},
                {'label': 'Mediator escrow redeem script',  'value': mediator_redeem_script},
             ]
    document = assemble_document('Bid', fields)
    res = sign_and_store_document(rein, 'bid', document, user.daddr, user.dkey, store)
    if res and store:
        click.echo("Bid created. Run 'rein sync' to push to available servers.")
    log.info('bid signed') if res else log.error('bid failed')


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.option('--defaults', '-d', default=None, help='file with form values')
@click.option('--dry-run/--no-dry-run', '-n', default=False, help='generate but do not store document')
def offer(multi, identity, defaults, dry_run):
    """
    Award a job.

    A job creator would use this command to award the job to a specific bid. 
    Once signed and pushed, escrow addresses should be funded by the job
    creator. Then the job creator should contact the worker and after the
    worker verifies the payments are correct, work can begin.
    """
    (log, user, key, urls) = init(multi, identity)
    form = {}
    if defaults:
        form = parse_document(open(defaults).read())
        if 'Title' in form and form['Title'] != 'Rein Offer':
            return click.echo("Input file type: " + form['Title'])
    store = False if dry_run else True

    bids = []
    for url in urls:
        sel_url = "{0}query?owner={1}&delegate={2}&query=bids&testnet={3}"
        data = safe_get(log, sel_url.format(url, user.maddr, user.daddr, rein.testnet))
        bids += filter_and_parse_valid_sigs(rein, data['bids'])

    unique_bids = unique(bids, 'Description')

    bids = []
    for bid in unique_bids:
        order = Order.get_by_job_id(rein, bid['Job ID'])
        if not order:
            order = Order(bid['Job ID'], testnet=rein.testnet)
            rein.session.add(order)
            rein.session.commit()
        state = order.get_state(rein, Document)
        if state in ['bid', 'job_posting']:
            bids.append(bid)
    
    if len(bids) == 0:
        click.echo('None found')
        return

    if 'Worker public key' in form.keys():
        bid = select_by_form([bid], 'Worker public key', form)
    else:
        bid = bid_prompt(rein, bids)
    if not bid:
        return

    log.info('got bid to offer')
    fields = [
                {'label': 'Job name',                       'value_from': bid},
                {'label': 'Worker',                         'value_from': bid},
                {'label': 'Description',                    'value_from': bid},
                {'label': 'Bid amount (BTC)',               'value_from': bid},
                {'label': 'Primary escrow address',         'value_from': bid},
                {'label': 'Mediator escrow address',        'value_from': bid},
                {'label': 'Job ID',                         'value_from': bid},
                {'label': 'Job creator',                    'value_from': bid},
                {'label': 'Job creator public key',         'value_from': bid},
                {'label': 'Mediator public key',            'value_from': bid},
                {'label': 'Worker public key',              'value_from': bid},
                {'label': 'Primary escrow redeem script',   'value_from': bid},
                {'label': 'Mediator escrow redeem script',  'value_from': bid},
             ]
    document = assemble_document('Offer', fields)
    if not click.confirm('Are you sure you want to award this bid?'):
        return

    res = sign_and_store_document(rein, 'offer', document, user.daddr, user.dkey, store)
    if res and store:
        click.echo("Two funding addresses and corresponding redeem scripts have been created for\n"
                   "this job. When it is time to distribute payment, you would use the redeem\n"
                   "script and a tool like Rein's modified version of Coinb.in to build and sign\n"
                   "payment transactions. As long as there is no dispute, the job creator would\n"
                   "sign a transaction paying the worker all funds held by the primary escrow\n"
                   "address and the mediator all funds held by the mediator escrow address.\n")
        click.echo("Offer created. Run 'rein sync' to push to available servers.")
    log.info('offer signed') if res else log.error('offer failed')


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.option('--defaults', '-d', default=None, help='file with form values')
@click.option('--dry-run/--no-dry-run', '-n', default=False, help='generate but do not store document')
def deliver(multi, identity, defaults, dry_run):
    """
    Deliver on a job.

    Share deliverables with the creator of the job when completed. In the
    event of a dispute, mediators are advised to review the deliverables
    while deciding how to distribute funds.
    """
    (log, user, key, urls) = init(multi, identity)
    form = {}
    if defaults:
        form = parse_document(open(defaults).read())
        if 'Title' in form and form['Title'] != 'Rein Deliver':
            return click.echo("Input file type: " + form['Title'])
    store = False if dry_run else True


    not_our_orders = get_in_process_orders(rein, Document, key, 'Job creator public key', False)
    if len(not_our_orders) == 0:
        click.echo('None found')
        return

    if 'Job ID' in form.keys():
        doc = select_by_form(not_our_orders, 'Job ID', form)
    else:
        doc = delivery_prompt(rein, not_our_orders, 'Deliverables')
    if not doc:
        return

    log.info('got offer for delivery')
    redeemScript = doc['Primary escrow redeem script']
    mediatorRedeemScript = doc['Mediator escrow redeem script']
    mediator_daddr = str(P2PKHBitcoinAddress.from_pubkey(x(doc['Mediator public key'])))
    (payment_txins,payment_amount,payment_address,payment_sig) = partial_spend_p2sh(redeemScript,rein)
    (mediator_payment_txins,mediator_payment_amount,mediator_payment_address) = partial_spend_p2sh_mediator(mediatorRedeemScript,rein,mediator_daddr)
    fields = [
        {'label': 'Job name',                       'value_from': doc},
        {'label': 'Job ID',                         'value_from': doc},
        {'label': 'Deliverables',                   'value': form.deliverables.data},
        {'label': 'Bid amount (BTC)',               'value_from': doc},
        {'label': 'Primary escrow address',         'value_from': doc},
        {'label': 'Mediator escrow address',        'value_from': doc},
        {'label': 'Primary escrow redeem script',   'value_from': doc},
        {'label': 'Mediator escrow redeem script',  'value_from': doc},
        {'label': 'Worker public key',              'value_from': doc},
        {'label': 'Mediator public key',            'value_from': doc},
        {'label': 'Job creator public key',         'value_from': doc},
        {'label':'Primary payment inputs','value':payment_txins},
        {'label':'Primary payment amount','value':payment_amount},
        {'label':'Primary payment address','value':payment_address},
        {'label':'Primary payment signature','value':payment_sig},
        {'label':'Mediator payment inputs','value':mediator_payment_txins},
        {'label':'Mediator payment amount','value':mediator_payment_amount},
        {'label':'Mediator payment address','value':mediator_payment_address}
    ]
    document = assemble_document('Delivery', fields)
    if check_redeem_scripts(document):
        res = sign_and_store_document(rein, 'delivery', document, user.daddr, user.dkey, store)
        if res and store:
            click.echo("Delivery created. Run 'rein sync' to push to available servers.")
    else:
        click.echo("Incorrect redeem scripts. Check keys and their order in redeem script.")
        res = False
    log.info('delivery signed') if res else log.error('delivery failed')


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.option('--defaults', '-d', default=None, help='file with form values')
@click.option('--dry-run/--no-dry-run', '-n', default=False, help='generate but do not store document')
def accept(multi, identity, defaults, dry_run):
    """
    Accept a delivery.

    Review and accept deliveries for your jobs. Once a delivery is
    accpted, mediators are advised not to sign any tranasctions
    refunding the job creator.
    """
    (log, user, key, urls) = init(multi, identity)
    form = {}
    if defaults:
        form = parse_document(open(defaults).read())
        if 'Title' in form and form['Title'] != 'Rein Accept Delivery':
            return click.echo("Input file type: " + form['Title'])
    store = False if dry_run else True

    our_orders = get_in_process_orders(rein, Document, key, 'Job creator public key', True)
    if len(our_orders) == 0:
        click.echo('None found')
        return

    if 'Job ID' in form.keys():
        doc = select_by_form(our_orders, 'Job ID', form)
    else:
        doc = accept_prompt(rein, our_orders, "Deliverables")
    if not doc:
        return

    log.info('got delivery for accept')

    redeemScript = doc['Primary escrow redeem script']
    txins = doc['Primary payment inputs']
    amount = doc['Primary payment amount']
    daddr = doc['Primary payment address']
    worker_sig = doc['Primary payment signature']
    redeemScript_mediator = doc['Mediator escrow redeem script']
    txins_mediator = doc['Mediator payment inputs']
    amount_mediator = doc['Mediator payment amount']
    daddr_mediator = doc['Mediator payment address']
    (payment_txid,client_sig) = spend_p2sh(redeemScript,txins,[float(amount)],[daddr],worker_sig,rein)
    tx_for_mediator = partial_spend_p2sh_mediator_2(redeemScript_mediator,txins_mediator,float(amount_mediator),daddr_mediator,rein)
    
    fields = [
        {'label': 'Job name',                       'value_from': doc},
        {'label': 'Job ID',                         'value_from': doc},
        {'label': 'Primary escrow redeem script',   'value_from': doc},
        {'label': 'Mediator escrow redeem script',  'value_from': doc},
        {'label':'Primary payment inputs','value_from':doc},
        {'label':'Primary payment amount','value_from':doc},
        {'label':'Primary payment address','value_from':doc},
        {'label':'Primary payment signature','value_from':doc},
        {'label':'Primary payment txid','value':payment_txid},
        {'label':'Primary payment client signature','value':client_sig},
        {'label':'Mediator payment inputs','value_from':doc},
        {'label':'Mediator payment amount','value_from':doc},
        {'label':'Mediator payment address','value_from':doc},
        {'label':'Mediator payment client signature','value':tx_for_mediator}
    ]
    document = assemble_document('Accept Delivery', fields)
    click.echo('\n'+document+'\n')
    if click.confirm("Are you sure?"):
        res = sign_and_store_document(rein, 'accept', document, user.daddr, user.dkey, store)
        if res and store:
            click.echo("Accepted delivery. Run 'rein sync' to push to available servers.")
        log.info('accept signed') if res else log.error('accept failed')
    else:
        click.echo("Accept aborted.") 


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.option('--defaults', '-d', default=None, help='file with form values')
@click.option('--dry-run/--no-dry-run', '-n', default=False, help='generate but do not store document')
def creatordispute(multi, identity, defaults, dry_run):
    """
    File a dispute (as a job creator).

    If you are a job creator, file a dispute on a job, for example if the job is
    not done on time.
    """
    (log, user, key, urls) = init(multi, identity)
    form = {}
    if defaults:
        form = parse_document(open(defaults).read())
        if 'Title' in form and form['Title'] != 'Rein Dispute Delivery':
            return click.echo("Input file type: " + form['Title'])
    store = False if dry_run else True

    our_orders = get_in_process_orders(rein, Document, key, 'Job creator public key', True)
    if len(our_orders) == 0:
        click.echo('None found')
        return

    if 'Job ID' in form.keys():
        doc = select_by_form(our_orders, 'Job ID', form)
    else:
        doc = dispute_prompt(rein, our_orders, "Deliverables")
    if not doc:
        return

    log.info('got delivery for dispute')
    fields = [
                {'label': 'Job name',                       'value_from': doc},
                {'label': 'Job ID',                         'value_from': doc},
                {'label': 'Dispute detail',                 'not_null': form},
                {'label': 'Primary escrow redeem script',   'value_from': doc},
                {'label': 'Mediator escrow redeem script',  'value_from': doc},
        {'label': 'Job creator public key', 'value_from': doc},
        {'label': 'Worker public key', 'value_from': doc},
        {'label': 'Mediator public key', 'value_from':doc}
             ]
    document = assemble_document('Dispute Delivery', fields)
    res = sign_and_store_document(rein, 'creatordispute', document, user.daddr, user.dkey, store)
    if res and store:
        click.echo("Dispute signed by job creator. Run 'rein sync' to push to available servers.")
    log.info('creatordispute signed') if res else log.error('creatordispute failed')


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.option('--defaults', '-d', default=None, help='file with form values')
@click.option('--dry-run/--no-dry-run', '-n', default=False, help='generate but do not store document')
def workerdispute(multi, identity, defaults, dry_run):
    """
    File a dispute (as a worker).

    If you are a worker, file a dispute because the creator is
    unresponsive or does not accept work that fulfills the job
    specification, they would use this command to file a dispute.
    """
    (log, user, key, urls) = init(multi, identity)
    form = {}
    if defaults:
        form = parse_document(open(defaults).read())
        if 'Title' in form and form['Title'] != 'Rein Dispute Offer':
            return click.echo("Input file type: " + form['Title'])
    store = False if dry_run else True

    our_orders = get_in_process_orders(rein, Document, key, 'Worker public key', True)
    if len(our_orders) == 0:
        click.echo('None found')
        return

    if 'Job ID' in form.keys():
        doc = select_by_form(our_orders, 'Job ID', form)
    else:
        doc = dispute_prompt(rein, our_orders, 'Deliverables')
    if not doc:
        return

    log.info('got in-process job for dispute')
    fields = [
        {'label': 'Job name',                       'value_from': doc},
        {'label': 'Job ID',                         'value_from': doc},
        {'label': 'Dispute detail',                 'not_null': form},
        {'label': 'Primary escrow redeem script',   'value_from': doc},
        {'label': 'Mediator escrow redeem script',  'value_from': doc},
        {'label': 'Job creator public key', 'value_from': doc},
        {'label': 'Worker public key','value_from': doc},
        {'label': 'Mediator public key','value_from':doc}
             ]
    document = assemble_document('Dispute Offer', fields)
    res = sign_and_store_document(rein, 'workerdispute', document, user.daddr, user.dkey, store)
    if res and store:
        click.echo("Dispute signed by worker. Run 'rein sync' to push to available servers.")
    log.info('workerdispute signed') if res else log.error('workerdispute failed')


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.option('--defaults', '-d', default=None, help='file with form values')
@click.option('--dry-run/--no-dry-run', '-n', default=False, help='generate but do not store document')
def resolve(multi, identity, defaults, dry_run):
    """
    Resolve a dispute.

    For mediators who are party to a disputed transaction, this command
    enables you to review each step, post a decision and post signed payment
    transactions.
    """
    (log, user, key, urls) = init(multi, identity)
    form = {}
    if defaults:
        form = parse_document(open(defaults).read())
        if 'Title' in form and form['Title'] != 'Rein Dispute Resolution':
            return click.echo("Input file type: " + form['Title'])
    store = False if dry_run else True

    valid_results = []
    for url in urls:
        sel_url = "{0}query?owner={1}&query=review&mediator={2}&testnet={3}"
        data = safe_get(log, sel_url.format(url, user.maddr, key, rein.testnet))
        results = data['review']
        valid_results += filter_and_parse_valid_sigs(rein, results)

    valid_results = unique(valid_results, 'Job ID')

    job_ids = []
    for result in valid_results:
        if 'Job ID' in result and result['Job ID'] not in job_ids:
            job_ids.append(result['Job ID'])

    job_ids_string = ','.join(job_ids)
    valid_results = []
    for url in urls:
        sel_url = "{0}query?owner={1}&job_ids={2}&query=by_job_id&testnet={3}"
        data = safe_get(log, sel_url.format(url, user.maddr, job_ids_string, rein.testnet))
        if data and 'by_job_id' in data:
            results = data['by_job_id']
            valid_results += filter_and_parse_valid_sigs(rein, results, 'Dispute detail')

    valid_results = unique(valid_results, 'Job ID')
    if len(valid_results) == 0:
        click.echo('None found')
        return

    if 'Job ID' in form.keys():
        doc = select_by_form(valid_results, 'Job ID', form)
    else:
        doc = resolve_prompt(rein, valid_results)
    if not doc:
        return

    log.info('got disputes for resolve')
    redeemScript = doc['Primary escrow redeem script']
    mediatorRedeemScript = doc['Mediator escrow redeem script']
    mediator_daddr = rein.user.daddr
    worker_payment_daddr = str(P2PKHBitcoinAddress.from_pubkey(x(doc['Worker public key'])));
    client_payment_daddr = str(P2PKHBitcoinAddress.from_pubkey(x(doc['Job creator public key'])));
    client_payment_amount = float(click.prompt("Client payment amount"))
    (payment_txins,payment_amount_1,payment_address_1,payment_amount_2,payment_address_2,payment_sig) = partial_spend_p2sh(redeemScript,rein,worker_payment_daddr,client_payment_amount,client_payment_daddr)
    (mediator_payment_txins,mediator_payment_amount,mediator_payment_address,mediator_payment_sig) = partial_spend_p2sh_mediator(mediatorRedeemScript,rein,mediator_daddr,True)
    fields = [
        {'label': 'Job name',                       'value_from': doc},
        {'label': 'Job ID',                         'value_from': doc},
        {'label': 'Resolution',                     'not_null': form},
        {'label': 'Job creator public key', 'value_from': doc},
        {'label': 'Worker public key', 'value_from':doc},
        {'label': 'Mediator public key', 'value_from':doc},
        {'label': 'Primary escrow redeem script',   'value_from': doc},
        {'label': 'Mediator escrow redeem script',  'value_from': doc},
        {'label':'Primary payment inputs','value':payment_txins},
        {'label':'Primary worker payment amount','value':payment_amount_1},
        {'label':'Primary worker payment address','value':payment_address_1},
        {'label':'Primary client payment amount','value':payment_amount_2},
        {'label':'Primary client payment address','value':payment_address_2},
        {'label':'Primary payment signature','value':payment_sig},
        {'label':'Mediator payment inputs','value':mediator_payment_txins},
        {'label':'Mediator payment amount','value':mediator_payment_amount},
        {'label':'Mediator payment address','value':mediator_payment_address},
        {'label':'Mediator payment signature','value':mediator_payment_sig}
    ]
    document = assemble_document('Dispute Resolution', fields)
    res = sign_and_store_document(rein, 'resolve', document, user.daddr, user.dkey, store)
    if res and store:
        click.echo("Dispute resolution signed by mediator. Run 'rein sync' to push to available servers.")
    log.info('resolve signed') if res else log.error('resolve failed')

@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.option('--defaults', '-d', default=None, help='file with form values')
@click.option('--dry-run/--no-dry-run', '-n', default=False, help='generate but do not store document')
def acceptresolution(multi, identity, defaults, dry_run):

    (log, user, key, urls) = init(multi, identity)
    form = {}
    if defaults:
        form = parse_document(open(defaults).read())
        if 'Title' in form and form['Title'] != 'Rein Accept Resolution':
            return click.echo("Input file type: " + form['Title'])
    store = False if dry_run else True

    #our_orders = get_in_process_orders(rein, Document, key, 'Job creator public key', True)+get_in_process_orders(rein, Document, key, 'Worker public key', True)

    documents = Document.get_user_documents(rein)
    job_ids = []
    for document in documents:
        job_id = Document.get_job_id(document.contents)
        if job_id not in job_ids:
            if document.source_url == 'local' and document.doc_type != 'enrollment':
                job_ids.append(job_id)

    urls = Bucket.get_urls(rein)
    documents = []
    job_ids_string = ','.join(job_ids)
    valid_results = []
    for url in urls:
        sel_url = "{0}query?owner={1}&job_ids={2}&query=by_job_id&testnet={3}"
        data = safe_get(log, sel_url.format(url, user.maddr, job_ids_string, rein.testnet))
        if data and 'by_job_id' in data:
            results = data['by_job_id']
            valid_results += filter_and_parse_valid_sigs(rein, results, 'Resolution')
        
    valid_results = unique(valid_results, 'Job ID')
                                                        
    if len(valid_results) == 0:
        click.echo('None found')
        return

    if 'Job ID' in form.keys():
        doc = select_by_form(valid_results, 'Job ID', form)
    else:
        doc = acceptresolution_prompt(rein, valid_results, "Resolution")
    if not doc:
        return

    redeemScript = doc['Primary escrow redeem script']
    txins = doc['Primary payment inputs']
    amount1 = doc['Primary worker payment amount']
    daddr1 = doc['Primary worker payment address']
    amount2 = doc['Primary client payment amount']
    daddr2 = doc['Primary client payment address']
    sig_primary = doc['Primary payment signature']
    redeemScript_mediator = doc['Mediator escrow redeem script']
    txins_mediator = doc['Mediator payment inputs']
    amount_mediator = doc['Mediator payment amount']
    daddr_mediator = doc['Mediator payment address']
    sig_mediator = doc['Mediator payment signature']

    reverse_sigs = False
    if key == doc['Worker public key']:
        reverse_sigs = True
    (payment_txid,second_sig) = spend_p2sh(redeemScript,txins,[float(amount1),float(amount2)],[daddr1,daddr2],sig_primary,rein,reverse_sigs)
    (payment_txid_mediator,second_sig_mediator) = spend_p2sh_mediator(redeemScript_mediator,txins_mediator,[float(amount_mediator)],[daddr_mediator],sig_mediator,rein)

    fields = [
        {'label': 'Job name',                       'value_from': doc},
        {'label': 'Job ID',                         'value_from': doc},
        {'label': 'Primary escrow redeem script',   'value_from': doc},
        {'label': 'Mediator escrow redeem script',  'value_from': doc},
        {'label':'Primary payment inputs','value_from':doc},
        {'label':'Primary worker payment amount','value_from':doc},
        {'label':'Primary worker payment address','value_from':doc},
        {'label':'Primary client payment amount','value_from':doc},
        {'label':'Primary client payment address','value_from':doc},
        {'label':'Primary payment signature','value_from':doc},
        {'label':'Primary payment txid','value':payment_txid},
        {'label':'Primary payment second signature','value':second_sig},
        {'label':'Mediator payment inputs','value_from':doc},
        {'label':'Mediator payment amount','value_from':doc},
        {'label':'Mediator payment address','value_from':doc},
        {'label':'Mediator payment signature','value_from':doc},
        {'label':'Mediator payment txid','value':payment_txid_mediator},
        {'label':'Mediator payment second signature','value':second_sig_mediator}
    ]
    
    document = assemble_document('Accept Resolution', fields)
    click.echo('\n'+document+'\n')
    if click.confirm("Are you sure?"):
        res = sign_and_store_document(rein, 'acceptresolution', document, user.daddr, user.dkey, store)
        if res and store:
            click.echo("Accepted resolution. Run 'rein sync' to push to available servers.")
        log.info('accept resolution signed') if res else log.error('accept resolution failed')
    else:
        click.echo("Accept resolution aborted.")

@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.argument('url', required=True)
def request(multi, identity, url):
    """
    Request free microhosting space.

    During the alpha testing phase, reinproject.org will operate
    at least one free microhosting server. The goal is to incentivize
    a paid network of reliable microhosting servers to store and serve
    all data required for Rein to operate.
    """
    (log, user, key, urls) = init(multi, identity)

    click.echo("User: " + user.name)
    log.info('got user for request')

    if not url.endswith('/'):
        url += '/'
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url

    if Bucket.get_bucket_count(rein, url) > 4:
        click.echo("You already have enough (3) buckets from %s" % url)
        log.warning('too many buckets')
        return
    sel_url = "{0}request?owner={1}&delegate={2}&contact={3}"

    try:
        answer = requests.get(url=sel_url.format(url, user.maddr, user.daddr, user.contact), proxies=rein.proxies)
    except:
        click.echo('Error connecting to server.')
        log.error('server connect error ' + url)
        return

    if answer.status_code != 200:
        click.echo("Request failed. Please try again later or with a different server.")
        log.error('server returned error')
        return
    else:
        data = json.loads(answer.text)
        click.echo('Success, you have %s buckets at %s' % (str(len(data['buckets'])), url))
        log.info('server request successful')

    if 'result' in data and data['result'] == 'error':
        click.echo('The server returned an error: %s' % data['message'])

    for bucket in data['buckets']:
        b = rein.session.query(Bucket).filter(and_(Bucket.url == url, Bucket.date_created == bucket['created'])).first()
        if b is None:
            b = Bucket(url, user.id, bucket['id'], bucket['bytes_free'],
                       datetime.strptime(bucket['created'], '%Y-%m-%d %H:%M:%S'))
            rein.session.add(b)
            rein.session.commit()
        log.info('saved bucket created %s' % bucket['created'])


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.argument('url', required=True)
def buy(multi, identity, url):
    """
    Buy microhosting space.

    Purchase microhosting from one server out of a paid network of servers 
    which store and serve data required for Rein.
    """
    (log, user, key, urls) = init(multi, identity)

    click.echo("User: " + user.name)
    log.info('got user for request')

    if not url.endswith('/'):
        url = url + '/'
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url

    sel_url = "{0}buy?owner={1}&delegate={2}&contact={3}"

    try:
        answer = requests.get(url=sel_url.format(url, user.maddr, user.daddr, user.contact), proxies=rein.proxies)
    except:
        click.echo('Error connecting to server.')
        log.error('server connect error ' + url)
        return

    if answer.status_code != 200:
        click.echo("Buy failed. Please try again later or with a different server.")
        log.error('server returned error')
        return
    else:
        data = json.loads(answer.text)
        click.echo('Please pay %s BTC to %s to enable bucket at %s' % (str(data['price']), data['address'], url))
        log.info('server buy request successful')

    if 'result' in data and data['result'] == 'error':
        click.echo('The server returned an error: %s' % data['message'])

    # later need to check if bucket payment was received
    for bucket in data['buckets']:
        b = rein.session.query(Bucket).filter(and_(Bucket.url==url, Bucket.date_created==bucket['created'])).first()
        if b is None:
            b = Bucket(url, user.id, bucket['id'], bucket['bytes_free'],
                       datetime.strptime(bucket['created'], '%Y-%m-%d %H:%M:%S'))
            rein.session.add(b)
            rein.session.commit()
        log.info('saved buy bucket created %s' % bucket['created'])


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
def sync(multi, identity):
    """
    Upload records to each registered server.

    Each user, bid, offer, etc. (i.e. anything except actual payments) is 
    stored as document across a network of paid servers. This command pushes
    the documents you have created to the servers from which you have
    purchased microhosting.
    """
    (log, user, key, urls) = init(multi, identity)

    sync_core(log, user, key, urls)

def sync_core(log, user, key, urls):
    click.echo("User: " + user.name)

    if len(urls) == 0:
        click.echo("No buckets registered. Run 'rein request' to continue.")
        return

    mediators = remote_query(rein, user, urls, log, 'mediators', 'Mediator public key')
    for m in mediators:
        from pprint import pprint
        if 'Secure Identity Number' in m and not Mediator.get(m['Master signing address'], rein.testnet):
            newMediator = Mediator(m, testnet)
            rein.session.add(newMediator)
            rein.session.commit()

    documents = Document.get_user_documents(rein)
    if len(documents) == 0:
        click.echo("Nothing to do.")

    upload = []
    nonce = {}
    for url in urls:
        nonce[url] = get_new_nonce(rein, url)
        if nonce[url] is None:
            continue

        for doc in documents:
            if len(doc.contents) > 8192:
                click.echo('Document is too big. 8192 bytes should be enough for anyone.')
                log.error("Document oversized %s" % doc.doc_hash)
            else:
                placements = Placement.get_placements(rein, url, doc.id)
                           
                if len(placements) == 0:
                    upload.append([doc, url])
                else:
                    for plc in placements:
                        if Placement.get_remote_document_hash(rein, plc) != doc.doc_hash:
                            upload.append([doc, url])
    
    failed = []
    succeeded = 0
    for doc, url in upload:
        placements = Placement.get_placements(rein, url, doc.id)
        if len(placements) == 0:
            remote_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits)
                                 for _ in range(32))
            plc = Placement(doc.id, url, remote_key, False, rein.testnet)
            rein.session.add(plc)
            rein.session.commit()
        else:
            plc = placements[0]
            for p in placements[1:]:
                rein.session.delete(p)
                rein.session.commit()

        if len(doc.contents) > 8192:
            log.error("Document oversized %s" % doc.doc_hash)
            click.echo('Document is too big. 8192 bytes should be enough for anyone.')
        elif nonce[url] is None:
            continue
        else:
            message = plc.remote_key + doc.contents + user.daddr + nonce[url]
            message = message.decode('utf8')
            message = message.encode('ascii')
            signature = sign(user.dkey, message)
            data = {"key": plc.remote_key,
                    "value": doc.contents,
                    "nonce": nonce[url],
                    "signature": signature,
                    "signature_address": user.daddr,
                    "owner": user.maddr,
                    "testnet": rein.testnet}
            body = json.dumps(data)
            headers = {'Content-Type': 'application/json'}
            answer = requests.post(url='{0}put'.format(url), headers=headers, data=body, proxies=rein.proxies)
            res = answer.json()
            if 'result' not in res or res['result'] != 'success':
                log.error('upload failed doc=%s plc=%s url=%s res=%s' % (doc.id, plc.id, url, res))
                click.echo("Upload error: %s" % (res['error']))
                failed.append(doc)
            else:
                plc.verified += 1
                rein.session.commit()
                log.info('upload succeeded doc=%s plc=%s url=%s' % (doc.id, plc.id, url))
                click.echo('uploaded %s' % doc.doc_hash)
                succeeded += 1

    for url in urls:
        if nonce[url] is None:
            continue
        sel_url = url + 'nonce?address={0}&clear={1}'
        answer = safe_get(log, sel_url.format(user.maddr, nonce[url]))
        log.info('nonce cleared for %s' % (url))

    rein.session.commit()
    click.echo('%s docs checked on %s servers, %s uploads done.' % (len(documents), len(urls), str(succeeded)))

@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
def rate(multi, identity):
    """Rate users that participated in past jobs"""
    (log, user, key, urls) = init(multi, identity)
    user_jobs = get_user_jobs(rein, True)

    i = 1
    for job in user_jobs:
        click.echo('{}: {} - {}'.format(i, job['job_id'], job['job_name']))
        i += 1

    job_choice = click.prompt('Please select a job you wish to rate a user\'s performance for')
    job = None
    try:
        job = user_jobs[int(job_choice) - 1]

    except:
        click.echo('Your choice was not valid.')
        return

    if not job:
        click.echo('Something went wrong. Try again.')
        return

    i = 1
    positions = ['employer', 'mediator', 'employee']
    for rated_user in positions:
        click.echo('{}: {} - {}'.format(i, job[rated_user]['SIN'], job[rated_user]['Name']))
        i += 1

    user_choice = click.prompt('Please select a user whose performance you\'d like to rate')
    rated_user = None
    try:
        rated_user = job[positions[int(user_choice) - 1]]

    except:
        click.echo('Your choice was not valid.')
        return

    if not rated_user:
        click.echo('Something went wrong. Try again.')
        return

    rating = click.prompt('Please enter a rating from 0 to 5 for {}'.format(rated_user['Name']))

    valid = False
    try:
        if int(rating) in range(0, 6):
            valid = True

    except:
        click.echo('Your choice was not valid.')
        return

    comments = click.prompt('If you so desire, you can add a comment (<100 characters) regarding the user\'s performance')

    if len(comments) > 100:
        click.echo('Your comment was too long. Please try again and stay below 100 characters.')
        return

    if rated_user['SIN'] == user.msin:
        click.echo('You cannot rate yourself.')
        return

    if valid:
        add_rating(rein, user, rein.testnet, rating, rated_user['SIN'], job['job_id'], user.msin, comments)
        click.echo('The rating was successfully created. Please sync the changes to available servers by using rein sync.')
        return

    click.echo('Something went wrong. Please try again.')
    return


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.option('--jobid', default=None, help="ID of job, dumps documents to screen")
def status(multi, identity, jobid):
    """
    Show user info and active jobs.
    """
    (log, user, key, urls) = init(multi, identity)

    Order.update_orders(rein, Document)
    documents = Document.get_user_documents(rein)

    if jobid is None:
        click.echo("User: %s" % user.name)
        click.echo("Master bitcoin address: %s" % user.maddr)
        click.echo("Delegate bitcoin address: %s" % user.daddr)
        click.echo("Delegate public key: %s" % key)
        click.echo("Willing to mediate: %s" % user.will_mediate)
        if user.will_mediate: 
            click.echo("Mediator fee: %s %%" % user.mediator_fee)
        click.echo("Total document count: %s" % len(documents))   
        click.echo("Registered servers: ")
        for url in urls:
            click.echo("  " + url)
        click.echo("Testnet: %s" % PersistConfig.get(rein, 'testnet'))
        click.echo("Tor: %s" % PersistConfig.get(rein, 'tor'))
        click.echo('')
        click.echo('ID  Job ID                 Status')
        click.echo('-----------------------------------------------------')
        orders = Order.get_user_orders(rein, Document)
        for order in orders:
            past_tense = order.get_past_tense(order.get_state(rein, Document))
            click.echo("%s   %s   %s" % (order.id, order.job_id, past_tense))
    else:
        remote_documents = []
        for url in urls:    
            sel_url = "{0}query?owner={1}&query=by_job_id&job_ids={2}&testnet={3}"
            data = safe_get(log, sel_url.format(url, user.maddr, jobid, rein.testnet))
            remote_documents += filter_and_parse_valid_sigs(rein, data['by_job_id'])
        unique_documents = unique(remote_documents)
        combined = {}
        for doc in remote_documents:
            combined.update(doc)

        cleanup = ['Title', 'signature', 'signature_address', 'valid']
        for key in cleanup:
            if key in combined:
                del combined[key]
        pprint(combined)
        if len(remote_documents) == 0:
            order = Order.get_by_job_id(rein, jobid)
            if order:
                documents = order.get_documents(rein, Document)
                for document in documents:
                    click.echo("\n" + document.contents)
            else:
                click.echo("Job id not found")


@cli.command()
@click.argument('key', required=True)
@click.argument('value', required=True)
def config(key, value):
    """
    Set configuration variable. Parses true/false, on/off, and passes
    anything else unaltered to the db.
    """
    keys = ['testnet', 'tor', 'debug', 'fee']
    if key not in keys:
        click.echo("Invalid config setting. Try one of " + ', '.join(keys))
        return

    if value and value.lower() in ['on', 'true', 'enabled']:
        PersistConfig.set(rein, key, 'true')
    elif value and value.lower() in ['off', 'false', 'disabled']:
        PersistConfig.set(rein, key, 'false')
    else:
        PersistConfig.set(rein, key, value)


# leave specific config commands in for backwards compatibility, remove in 0.4
@cli.command()
@click.argument('testnet', required=True)
def testnet(testnet):
    """
    Enter 'true' / 'false' to toggle testnet mode.

    Testnet is a separate key-value namespace both locally and on
    available Causeway servers where contracts are assumed to be
    for testing, and non-binding.
    """
    if testnet and testnet.lower() == 'true':
        PersistConfig.set(rein, 'testnet', 'true')
        click.echo("Testnet enabled.")
    else:
        PersistConfig.set(rein, 'testnet', 'false')
        click.echo("Testnet disabled.")
    return


@cli.command()
@click.argument('tor', required=True)
def tor(tor):
    """
    Enter 'true' / 'false' etc to toggle connection through Tor.
    """
    if tor and tor.lower() in ['on', 'true', 'enabled']:
        PersistConfig.set(rein, 'tor', 'true')
        click.echo("Tor enabled.")
    elif tor and tor.lower() in ['off', 'false', 'disabled']:
        PersistConfig.set(rein, 'tor', 'false')
        click.echo("Tor disabled.")
    else:
        click.echo("Invalid option.")
    return

@cli.command()
@click.argument('debug', required=True)
def debug(debug):
    """
    Enter 'true' / 'false' etc to toggle debug mode on startup.
    """
    if debug and debug.lower() in ['on', 'true', 'enabled']:
        PersistConfig.set(rein, 'debug', 'true')
        click.echo("Debug enabled.")
    elif debug and debug.lower() in ['off', 'false', 'disabled']:
        PersistConfig.set(rein, 'debug', 'false')
        click.echo("Debug disabled.")
    else:
        click.echo("Invalid option.")
    return


def init(multi, identity):
    log = rein.get_log()
    if multi:
        rein.set_multiuser()
    if rein.has_no_account():
        click.echo("Please run setup.")
        return sys.exit(1)
    user = get_user(rein, identity, True)
    key = pubkey(user.dkey)
    urls = Bucket.get_urls(rein)
    return (log, user, key, urls)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def is_tags(s):
    if re.search(r'[^a-z0-9 ,]', s.lower()):
        return False
    else:
        return True

def get_user(rein, identity, enrolled):
    if rein.multi and identity:
        rein.user = rein.session.query(User).filter(
                            and_(User.name == identity,
                                 User.enrolled == enrolled,
                                 User.testnet == rein.testnet)).first()
    elif rein.multi:
        rein.user = identity_prompt(rein)
    else:
        rein.user = rein.session.query(User).filter(
                            and_(User.enrolled == enrolled,
                                 User.testnet == rein.testnet)).first()
    return rein.user


def get_new_nonce(rein, url):
    sel_url = url + 'nonce?address={0}'
    try:
        answer = requests.get(url=sel_url.format(rein.user.maddr), proxies=rein.proxies)
    except requests.exceptions.ConnectionError:
        click.echo('Could not reach %s.' % url)
        return None
    data = answer.json()
    rein.log.info('server returned nonce %s' % data['nonce'])
    return data['nonce']


def select_by_form(candidates, field, form):
   """
   Iterate through array of dicts to match a key/value. 
   """
   if field in form.keys():
       for candidate in candidates:
           if candidate[field] == form[field]:
               return candidate
       click.echo(field + ' not found on available servers.')
       return None
   else:
       click.echo(field + " is required but not in your defaults file")


@cli.command()
@click.option('--multi/--no-multi', '-m', default=False, help="prompt for identity to use")
@click.option('--identity', '-i', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.option('--setup/--no-setup', default=False, help="Setup new user")
def start(multi, identity, setup):
    """
    Use Rein from the browser.

    Starts a local web server and opens a browser with
    simple UI to use Rein.
    """
    import webbrowser
    from flask import Flask, request, redirect, url_for, flash, send_from_directory, render_template, jsonify
    from .lib.forms import JobPostForm, BidForm, JobOfferForm, DeliverForm, AcceptForm, DisputeForm, ResolveForm, AcceptResolutionForm, RatingForm
    from .lib.mediator import Mediator
    import rein.lib.crypto.bip32 as bip32
    from .lib.ui import build_enrollment_from_dict
    from .lib.bitcoinecdsa import sign
    from .lib.bitcoinaddress import generate_sin

    host = '127.0.0.1'
    port = 5001

    tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html')

    app = Flask(__name__, template_folder=tmpl_dir)
    app.secret_key = ''.join(random.SystemRandom().choice(string.digits) for _ in range(32))

    def flash_errors(form):
        for field, errors in form.errors.items():
            for error in errors:
                flash(u"Error in the %s field - %s" % (
                    getattr(form, field).label.text,
                    error
                ))

    @app.route('/setup')
    def web_setup():
        return render_template('setup.html')

    @app.route('/generate-mnemonic', methods=['GET'])
    def generate_mnemonic_url():
        try:
            return json.dumps({'mnemonic':(' '.join(bip32.generate_mnemonic(128)))})
        except Exception as exc:
            import traceback
            print(traceback.format_exc())
            to_return = {'enrolled': False,
                         'exception': str(exc)}
            print(exc)
            return json.dumps(to_return)
    
    @app.route('/register-user', methods=['POST'])
    def register_user():
        try:
            # Generate user data
            mnemonic_list = str(request.form['mnemonic']).split()
            mnemonic_list_unicode = [s.decode('unicode-escape') for s in mnemonic_list]
            key = bip32.mnemonic_to_key(mnemonic_list_unicode)
            mprv = bip32.get_master_private_key(key)
            maddr = bip32.get_master_address(key)
            daddr = bip32.get_delegate_address(key)
            dkey = bip32.get_delegate_private_key(key)
            dxprv = bip32.get_delegate_extended_key(key)
            msin = generate_sin(maddr)

            # Check mediator status
            if request.form['mediate'] == "True":
                will_mediate = True
            else:
                will_mediate = False

            user_data = {'name': request.form['name'],
                        'contact': request.form['contact'],
                        'maddr': maddr,
                        'daddr': daddr,
                        'dkey': dkey,
                        'dxprv': dxprv,
                        'will_mediate': will_mediate,
                        'mediator_fee': request.form['mediatorFee'].replace('%',''),
                        'msin': msin,
                        'testnet': rein.testnet}
            new_identity = User(user_data)
            rein.user = new_identity
            rein.session.add(new_identity)
            rein.session.commit()
            
            # Enroll user
            enrollment = build_enrollment_from_dict(user_data)
            signed_enrollment = '-----BEGIN BITCOIN SIGNED MESSAGE-----\n' + \
                                enrollment + \
                                '\n-----BEGIN SIGNATURE-----\n' + \
                                maddr + '\n' + \
                                sign(mprv, enrollment) + \
                                '\n-----END BITCOIN SIGNED MESSAGE-----\n'
            User.set_enrolled(rein, new_identity)
            document = Document(rein, 'enrollment', signed_enrollment, sig_verified=True, testnet=rein.testnet)
            rein.session.add(document)
            rein.session.commit()
            return json.dumps({'enrolled': True})
        except Exception as exc:
            import traceback
            print(traceback.format_exc())
            to_return = {'enrolled': False,
                         'exception': str(exc)}
            print(exc)
            return json.dumps(to_return)

    @app.route('/setup')
    def setup2():
        return render_template('setup.html')

    def shutdown_server():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    @app.route("/done")
    def start_done():
        shutdown_server()
        return render_template("done.html")

    @app.route('/exit')
    def make_like_a_tree():
        shutdown_server()
        return "Server shutting down... Thank you for using Rein."

    @app.route('/<path:path>')
    def serve_static_file(path):
        return send_from_directory(tmpl_dir, path)

    if rein.has_no_account() or setup:
        webbrowser.open('http://'+host+':' + str(port) + '/setup')
        app.run(host=host, port=port, debug=rein.debug)
        return
    else:
        (log, user, key, urls) = init(multi, identity)
        documents = Document.get_user_documents(rein)
        orders = Order.get_user_orders(rein, Document)
        bids = Document.get_by_type(rein, 'bid')
        jobs = []
        blocks = []
        connected = False
        for url in urls:
            sel_url = "{0}query?owner={1}&query=jobs&testnet={2}"
            data = safe_get(log, sel_url.format(url, user.maddr, rein.testnet))
            if not data or 'block_info' not in data:
                continue
            connected = True
            blocks.append(data['block_info'])
            jobs += filter_and_parse_valid_sigs(rein, data['jobs'])
        if not connected:
            click.echo('No servers were available. Please check your internet connection.')
            log.error('no servers available')
            return
        (block_hash, block_time) = choose_best_block(blocks)
        t = time.localtime()
        dst_offset = 3600 * t.tm_isdst
        str_block_time = datetime.fromtimestamp(block_time + time.timezone - dst_offset).strftime('%Y-%m-%d %H:%M:%S %Z')
        time_offset = abs(block_time - int(time.time()))

    @app.route('/rate', methods=['POST', 'GET'])
    def rate_web():
        form = RatingForm(request.form)

        if request.method == 'POST' and form.validate_on_submit():
            (rating, user_msin, job_id, rated_by_msin, comments) = (form.rating.data, form.user_id.data, form.job_id.data, form.rated_by_id.data, form.comments.data)
            sync_rating = add_rating(rein, user, rein.testnet, rating, user_msin, job_id, rated_by_msin, comments)
            if sync_rating:
                click.echo("Rating created.")
                sync_core(log, user, key, urls)

            return redirect("/rate")

        elif request.method == 'POST':
            flash_errors(form)
            return redirect("/rate")

        else:
            user_jobs = get_user_jobs(rein)
            return render_template("rate.html", form=form, user_sin=user.msin, user=user, user_jobs=user_jobs)

    @app.route("/post", methods=['POST', 'GET'])
    def job_post():
        form = JobPostForm(request.form)

        eligible_mediators = []
        for url in urls:
            sel_url = "{0}query?owner={1}&query=mediators&testnet={2}"
            data = safe_get(log, sel_url.format(url, user.maddr, rein.testnet))
            if data:
                eligible_mediators += filter_and_parse_valid_sigs(rein,
                                                                  data['mediators'],
                                                                  "Secure Identity Number")

        for e in eligible_mediators:
            if not Mediator.get(e['Master signing address'], rein.testnet):
                m = Mediator(e, rein.testnet)
                rein.session.add(m)
                rein.session.commit()

        mediators = Mediator.get(None, rein.testnet)
        mediator_maddrs = []
        for m in mediators:
            if m.dpubkey != key:
                mediator_maddrs.append((m.maddr, '{}</td><td>{}</td><td>{}%</td><td><a href="mailto:{}" target="_blank">{}</a></td><td>{}'.\
                        format(m.username,
                               get_averave_user_rating_display(log, url, user, rein, m.msin),
                               m.mediator_fee,
                               m.contact,
                               m.contact,
                               m.dpubkey)))

        form.mediator_maddr.choices = mediator_maddrs

        no_choices = len(mediator_maddrs) == 0

        if request.method == 'POST' and form.validate_on_submit():
            mediator = Mediator.get(form.mediator_maddr.data, rein.testnet)[0]
            job_guid = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(20))
            fields = [
                {'label': 'Job name',                       'value': form.job_name.data,
                    'help': 'Choose a brief but descriptive name for the job.'},
                {'label': 'Job ID',                         'value': job_guid},
                {'label': 'Tags',                           'value': form.tags.data,
                    'help': 'Each post can have a set of tags associated with it. Though not implemented yet,\n'
                            'these tags may be used in searches and filters later. No spaces, dashes, or\n'
                            'special characters are allowed. Please enter them as a comma-separated list.\n'
                            'Example: software, 3dprinting'},
                {'label': 'Description',                    'value': form.description.data},
                {'label': 'Block hash',                     'value': block_hash},
                {'label': 'Time',                           'value': str(block_time)},
                {'label': 'Expiration (days)',              'value': form.expire_days.data},
                {'label': 'Mediator',                       'value': mediator.username},
                {'label': 'Mediator contact',               'value': mediator.contact},
                {'label': 'Mediator fee',                   'value': str(mediator.mediator_fee)},
                {'label': 'Mediator public key',            'value': mediator.dpubkey},
                {'label': 'Mediator delegate address',      'value': mediator.daddr},
                {'label': 'Mediator master address',        'value': mediator.maddr},
                {'label': 'Job creator',                    'value': user.name},
                {'label': 'Job creator contact',            'value': user.contact},
                {'label': 'Job creator public key',         'value': key},
                {'label': 'Job creator delegate address',   'value': user.daddr},
                {'label': 'Job creator master address',     'value': user.maddr},
                     ]
            document_text = assemble_document('Job', fields)
            store = True
            document = sign_and_store_document(rein, 'job_posting', document_text, user.daddr, user.dkey, store)
            if document and store:
                click.echo("Posting created.")
                sync_core(log, user, key, urls)
                flash("Posting created and pushed to available servers.")
            assemble_order(rein, document)
            log.info('posting signed') if document else log.error('posting failed')
            return redirect("/")
        elif request.method == 'POST':
            flash_errors(form)
            return redirect("/post")
        else:
            return render_template("post.html",
                            form=form,
                            user=user,
                            key=key,
                            urls=urls,
                            documents=documents,
                            orders=orders,
                            mediators=mediators,
                            block_time=str_block_time,
                            no_choices=no_choices,
                            time_offset=time_offset
                            )


    @app.route("/offer", methods=['POST', 'GET'])
    def job_offer():
        Order.update_orders(rein, Document)
        form = JobOfferForm(request.form)
        key = pubkey(rein.user.dkey)

        # get and store bids on our jobs
        bids = []
        for url in urls:
            sel_url = "{0}query?owner={1}&delegate={2}&query=bids&testnet={3}"
            data = safe_get(log, sel_url.format(url, user.maddr, user.daddr, rein.testnet))
            if data and 'bids' in data:
                bids += filter_and_parse_valid_sigs(rein, data['bids'])

        unique_bids = unique(bids, 'Description')

        bids = []
        for bid in unique_bids:
            if bid['Job creator public key'] != key:
                continue

            order = Order.get_by_job_id(rein, bid['Job ID'])

            if not order:
                order = Order(bid['Job ID'], testnet=rein.testnet)
                rein.session.add(order)
                rein.session.commit()

            state = order.get_state(rein, Document)

            if state in ['bid', 'job_posting']:
                bids.append(bid)

        # check of bid exists and if not store it
        # build tuple list to populate form.bids
        bid_choices = []
        for b in bids:
            worker_msin = generate_sin(b['Worker master address'])
            doc_hash = Document.calc_hash(b['original'])
            d = Document.find(rein, doc_hash, 'remote')
            if not d:
                d = Document(rein, 'bid', b['original'], source_url='remote', testnet=rein.testnet)
                rein.session.add(d)
                rein.session.commit()
                id = d.id
            else:
                id = d[0].id
            bid_choices.append((
                str(id), 
                '{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}'.format(
                    job_link(b),
                    b['Worker'],
                    get_averave_user_rating_display(log, url, user, rein, worker_msin),
                    b['Description'],
                    b['Bid amount (BTC)']
                )
                ))

        form.bid_id.choices = bid_choices

        no_choices = len(bid_choices) == 0

        if request.method == 'POST' and form.validate_on_submit():
            bid_doc = Document.get(rein, form.bid_id.data)
            bid = parse_document(bid_doc.contents)
            fields = [
                {'label': 'Job name',                       'value': bid['Job name']},
                {'label': 'Job ID',                         'value': bid['Job ID']},
                {'label': 'Description',                    'value': bid['Description']},
                {'label': 'Bid amount (BTC)',               'value': bid['Bid amount (BTC)']},
                {'label': 'Primary escrow address',         'value': bid['Primary escrow address']},
                {'label': 'Mediator escrow address',        'value': bid['Mediator escrow address']},
                {'label': 'Job creator',                    'value': bid['Job creator']},
                {'label': 'Job creator public key',         'value': bid['Job creator public key']},
                {'label': 'Mediator public key',            'value': bid['Mediator public key']},
                {'label': 'Worker public key',              'value': bid['Worker public key']},
                {'label': 'Primary escrow redeem script',   'value': bid['Primary escrow redeem script']},
                {'label': 'Mediator escrow redeem script',  'value': bid['Mediator escrow redeem script']},
                     ]
            document_text = assemble_document('Offer', fields)
            store = True
            document = sign_and_store_document(rein, 'offer', document_text, user.daddr, user.dkey, store)
            if document and store:
                click.echo("Offer created.")
                sync_core(log, user, key, urls)
                flash("Offer created and pushed to available servers.")
            assemble_order(rein, document)
            log.info('offer signed') if document else log.error('offer failed')
            return redirect("/")
        elif request.method == 'POST':
            flash_errors(form)
            return redirect("/offer")
        else:
            return render_template("offer.html",
                            form=form,
                            user=user,
                            key=key,
                            urls=urls,
                            documents=documents,
                            orders=orders,
                            bids=bids,
                            block_time=str_block_time,
                            no_choices=no_choices,
                            time_offset=time_offset
                            )


    @app.route("/accept", methods=['POST', 'GET'])
    def job_accept():
        Order.update_orders(rein, Document)
        form = AcceptForm(request.form)

        our_orders = get_in_process_orders(rein, Document, key, 'Job creator public key', True)

        deliverables = []
        for o in our_orders:
            doc_hash = Document.calc_hash(o['original'])
            d = Document.find(rein, doc_hash, 'remote')
            if d:
                id = d[0].id
            else:
                doc_type = Document.get_document_type(o['original'])
                d = Document(rein, doc_type, o['original'], source_url='remote', testnet=rein.testnet)
                rein.session.add(d)
                rein.session.commit()
                id = d.id
            if o['state'] in ['offer', 'delivery']:
                if 'Deliverables' in o:
                    delivery = o['Deliverables']
                else:
                    delivery = 'No deliveries found.'
                deliverables.append((str(id), '{}</td><td>{}'.format( job_link(o),
                                                                      delivery,
                                                                    )))
        no_choices = len(deliverables) == 0

        form.deliverable_id.choices = deliverables

        if request.method == 'POST' and form.validate_on_submit():
            delivery_doc = Document.get(rein, form.deliverable_id.data)
            delivery = parse_document(delivery_doc.contents)
            redeemScript = delivery['Primary escrow redeem script']
            txins = delivery['Primary payment inputs']
            amount = delivery['Primary payment amount']
            daddr = delivery['Primary payment address']
            worker_sig = delivery['Primary payment signature']
            redeemScript_mediator = delivery['Mediator escrow redeem script']
            txins_mediator = delivery['Mediator payment inputs']
            amount_mediator = delivery['Mediator payment amount']
            daddr_mediator = delivery['Mediator payment address']
            (payment_txid,client_sig) = spend_p2sh(redeemScript,txins,[float(amount)],[daddr],worker_sig,rein)
            tx_for_mediator = partial_spend_p2sh_mediator_2(redeemScript_mediator,txins_mediator,float(amount_mediator),daddr_mediator,rein)
            fields = [
                {'label': 'Job name',                       'value_from': delivery},
                {'label': 'Job ID',                         'value_from': delivery},
                {'label': 'Primary escrow redeem script',   'value_from': delivery},
                {'label': 'Mediator escrow redeem script',  'value_from': delivery},
                {'label':'Primary payment inputs','value_from':delivery},
                {'label':'Primary payment amount','value_from':delivery},
                {'label':'Primary payment address','value_from':delivery},
                {'label':'Primary payment signature','value_from':delivery},
                {'label':'Primary payment txid','value':payment_txid},
                {'label':'Primary payment client signature','value':client_sig},
                {'label':'Mediator payment inputs','value_from':delivery},
                {'label':'Mediator payment amount','value_from':delivery},
                {'label':'Mediator payment address','value_from':delivery},
                {'label':'Mediator payment client signature','value':tx_for_mediator}
                     ]

            document_text = assemble_document('Accept Delivery', fields)
            store = True
            document = sign_and_store_document(rein, 'accept', document_text, user.daddr, user.dkey, store)
            if document and store:
                click.echo("Accept created.")
                sync_core(log, user, key, urls)
                flash("Accept signed and pushed to available servers.")
            assemble_order(rein, document)
            log.info('accept signed') if document else log.error('accept failed')
            return redirect("/")
        elif request.method == 'POST':
            print("form data " + str(form))
            flash_errors(form)
            return redirect("/accept")
        else:
            return render_template("accept.html",
                            form=form,
                            user=user,
                            key=key,
                            urls=urls,
                            block_time=str_block_time,
                            no_choices=no_choices,
                            time_offset=time_offset
                            )

    @app.route("/acceptresolution", methods=['POST', 'GET'])
    def job_acceptresolution():

        form = AcceptResolutionForm(request.form)

        documents = Document.get_user_documents(rein)
        job_ids = []
        for document in documents:
            job_id = Document.get_job_id(document.contents)
            if job_id not in job_ids:
                if document.source_url == 'local' and document.doc_type != 'enrollment':
                    job_ids.append(job_id)

        urls = Bucket.get_urls(rein)
        documents = []
        job_ids_string = ','.join(job_ids)
        valid_results = []
        for url in urls:
            sel_url = "{0}query?owner={1}&job_ids={2}&query=by_job_id&testnet={3}"
            data = safe_get(log, sel_url.format(url, user.maddr, job_ids_string, rein.testnet))
            if data and 'by_job_id' in data:
                results = data['by_job_id']
                valid_results += filter_and_parse_valid_sigs(rein, results, 'Resolution')
                    
        valid_results = unique(valid_results, 'Job ID')

        resolutions = []
        for result in valid_results:
            order = Order.get_by_job_id(rein, result['Job ID'])

            if not order:
                order = Order(result['Job ID'], testnet=rein.testnet)
                rein.session.add(order)
                rein.session.commit()

            state = order.get_state(rein, Document)

            if state in ['resolve']:
                resolutions.append((result['Job ID'], '{}</td><td>{}'.format( job_link(result), result['Resolution'] )))

                
        no_choices = len(resolutions) == 0
        form.resolution_id.choices = unique(resolutions)
        
        if request.method == 'POST' and form.validate_on_submit():
            delivery = None
            for u in valid_results:
                if u['Job ID'] == form.resolution_id.data:
                    delivery = u
            redeemScript = delivery['Primary escrow redeem script']
            txins = delivery['Primary payment inputs']
            amount1 = delivery['Primary worker payment amount']
            daddr1 = delivery['Primary worker payment address']
            amount2 = delivery['Primary client payment amount']
            daddr2 = delivery['Primary client payment address']
            sig_primary = delivery['Primary payment signature']
            redeemScript_mediator = delivery['Mediator escrow redeem script']
            txins_mediator = delivery['Mediator payment inputs']
            amount_mediator = delivery['Mediator payment amount']
            daddr_mediator = delivery['Mediator payment address']
            sig_mediator = delivery['Mediator payment signature']

            reverse_sigs = False
            if key == delivery['Worker public key']:
                reverse_sigs = True
            (payment_txid,second_sig) = spend_p2sh(redeemScript,txins,[float(amount1),float(amount2)],[daddr1,daddr2],sig_primary,rein,reverse_sigs)
            (payment_txid_mediator,second_sig_mediator) = spend_p2sh_mediator(redeemScript_mediator,txins_mediator,[float(amount_mediator)],[daddr_mediator],sig_mediator,rein)
            fields = [
                {'label': 'Job name',                       'value_from': delivery},
                {'label': 'Job ID',                         'value_from': delivery},
                {'label': 'Primary escrow redeem script',   'value_from': delivery},
                {'label': 'Mediator escrow redeem script',  'value_from': delivery},
                {'label':'Primary payment inputs','value_from':delivery},
                {'label':'Primary worker payment amount','value_from':delivery},
                {'label':'Primary worker payment address','value_from':delivery},
                {'label':'Primary client payment amount','value_from':delivery},
                {'label':'Primary client payment address','value_from':delivery},
                {'label':'Primary payment signature','value_from':delivery},
                {'label':'Primary payment txid','value':payment_txid},
                {'label':'Primary payment second signature','value':second_sig},
                {'label':'Mediator payment inputs','value_from':delivery},
                {'label':'Mediator payment amount','value_from':delivery},
                {'label':'Mediator payment address','value_from':delivery},
                {'label':'Mediator payment signature','value_from':delivery},
                {'label':'Mediator payment txid','value':payment_txid_mediator},
                {'label':'Mediator payment second signature','value':second_sig_mediator}
            ]
            
            document_text = assemble_document('Accept Resolution', fields)
            store = True
            document = sign_and_store_document(rein, 'acceptresolution', document_text, user.daddr, user.dkey, store)
            if document and store:
                click.echo("Accept Resolution created.")
                sync_core(log, user, key, urls)
                flash("Accept Resolution signed and pushed to available servers.")
            assemble_order(rein, document)
            log.info('accept resolution signed') if document else log.error('accept resolution failed')
            return redirect("/")
        elif request.method == 'POST':
            print("form data " + str(form))
            flash_errors(form)
            return redirect("/acceptresolution")
        else:
            return render_template("acceptresolution.html",
                                   form=form,
                                user=user,
                                   key=key,
                                   urls=urls,
                                   block_time=str_block_time,
                                   no_choices=no_choices,
                                time_offset=time_offset
            )
                    
                                                                


    @app.route("/resolve", methods=['POST', 'GET'])
    def job_resolve():
        form = ResolveForm(request.form)

        # ask servers for jobs user is mediator for
        # this won't return disputes since they don't have mediator pubkey
        review = []
        for url in urls:
            sel_url = "{}query?owner={}&delegate={}&mediator={}&query=review&testnet={}"
            data = safe_get(log, sel_url.format(url, user.maddr, user.daddr, key, rein.testnet))
            if data and 'review' in data:
                review += filter_and_parse_valid_sigs(rein, data['review'])

        jobs_mediating = unique(review, 'Dispute detail')
        print(len(jobs_mediating))

        # store doc if we don't have it
        updated_jobs = []
        for u in jobs_mediating:
            doc_hash = Document.calc_hash(u['original'])
            d = Document.find(rein, doc_hash, 'remote')
            if not d:
                doc_type = Document.get_document_type(u['original'])
                d = Document(rein, doc_type, u['original'], source_url='remote', testnet=rein.testnet)
                rein.session.add(d)
                rein.session.commit()
                updated_jobs.append(u)

        Order.update_orders(rein, Document)

        # pull all docs for the new ones so we can figure out which need resolution
        disputes = []
        for u in jobs_mediating:
            order = Order.get_by_job_id(rein, u['Job ID'])

            if not order:
                order = Order(u['Job ID'], testnet=rein.testnet)
                rein.session.add(order)
                rein.session.commit()

            state = order.get_state(rein, Document)

            # add ones that need resolution to the choices
            # Note: removed requirement for state since it causes problems
            #dispute_docs = order.get_documents(rein, Document)
            #for d in dispute_docs:
                #doc = parse_document(d.contents)
            if 'Dispute detail' in u:
                disputes.append((u['Job ID'], '{}</td><td>{}'.format( job_link(u),
                                                                      u['Dispute detail']
                                                                  )))
        no_choices = len(disputes) == 0

        form.dispute_id.choices = unique(disputes)

        if request.method == 'POST' and form.validate_on_submit():
            dispute = None
            for u in jobs_mediating:
                if u['Job ID'] == form.dispute_id.data:
                    dispute = u
            redeemScript = dispute['Primary escrow redeem script']
            mediatorRedeemScript = dispute['Mediator escrow redeem script']
            mediator_daddr = rein.user.daddr
            worker_payment_daddr = str(P2PKHBitcoinAddress.from_pubkey(x(dispute['Worker public key'])));
            client_payment_daddr = str(P2PKHBitcoinAddress.from_pubkey(x(dispute['Job creator public key'])));
            client_payment_amount = float(form.client_payment_amount.data)
            try:
                (payment_txins,payment_amount_1,payment_address_1,payment_amount_2,payment_address_2,payment_sig) = partial_spend_p2sh(redeemScript,rein,worker_payment_daddr,client_payment_amount,client_payment_daddr)
                (mediator_payment_txins,mediator_payment_amount,mediator_payment_address,mediator_payment_sig) = partial_spend_p2sh_mediator(mediatorRedeemScript,rein,mediator_daddr,True)
            except ValueError as e:
                form.resolution.errors.append(e.message)
                flash_errors(form)
                return redirect("/resolve")
            fields = [
                {'label': 'Job name',                       'value_from': dispute},
                {'label': 'Job ID',                         'value_from': dispute},
                {'label': 'Resolution',                     'value': form.resolution.data},
                {'label': 'Job creator public key', 'value_from': dispute},
                {'label': 'Worker public key', 'value_from':dispute},
                {'label': 'Mediator public key', 'value_from':dispute},
                {'label': 'Primary escrow redeem script',   'value_from': dispute},
                {'label': 'Mediator escrow redeem script',  'value_from': dispute},
                {'label':'Primary payment inputs','value':payment_txins},
                {'label':'Primary worker payment amount','value':payment_amount_1},
                {'label':'Primary worker payment address','value':payment_address_1},
                {'label':'Primary client payment amount','value':payment_amount_2},
                {'label':'Primary client payment address','value':payment_address_2},
                {'label':'Primary payment signature','value':payment_sig},
                {'label':'Mediator payment inputs','value':mediator_payment_txins},
                {'label':'Mediator payment amount','value':mediator_payment_amount},
                {'label':'Mediator payment address','value':mediator_payment_address},
                {'label':'Mediator payment signature','value':mediator_payment_sig}
            ]
            document_text = assemble_document('Dispute Resolution', fields)
            store = True
            document = sign_and_store_document(rein, 'resolve', document_text, user.daddr, user.dkey, store)
            if document and store:
                click.echo("Dispute resolution created.")
                sync_core(log, user, key, urls)
                flash("Dispute resolution signed and pushed to available servers.")
            assemble_order(rein, document)
            log.info('resolve signed') if document else log.error('resolve failed')
            return redirect("/")
        elif request.method == 'POST':
            print("form data " + str(form))
            flash_errors(form)
            return redirect("/resolve")
        else:
            return render_template("resolve.html",
                            form=form,
                            user=user,
                            key=key,
                            urls=urls,
                            block_time=str_block_time,
                            no_choices=no_choices,
                            time_offset=time_offset
                            )

    @app.route('/job/<jobid>')
    def job_info_page(jobid):
        Order.update_orders(rein, Document)
        remote_documents = []
        for url in urls:    
            sel_url = "{0}query?owner={1}&query=by_job_id&job_ids={2}&testnet={3}"
            data = safe_get(log, sel_url.format(url, user.maddr, jobid, rein.testnet))
            if data and 'by_job_id' in data:
                remote_documents += filter_and_parse_valid_sigs(rein, data['by_job_id'])
        unique_documents = unique(remote_documents)
        combined = {}
        for doc in unique_documents:
            combined.update(doc)

        o = Order.get_by_job_id(rein, jobid)
        state = STATE[o.get_state(rein, Document)]

        cleanup = ['Title', 'signature', 'signature_address', 'valid']
        for key in cleanup:
            if key in combined:
                del combined[key]

        if len(remote_documents) == 0:
            found = False
        else:
            found = True

        try:
            if 'Bid amount (BTC)' in combined:
                mediator_fee_btc = str(round(float(combined['Bid amount (BTC)'])*float(combined['Mediator fee'])/100.,8))
            else:
                mediator_fee_btc = "NaN"
        except ValueError:
            mediator_fee_btc = "NaN"

        return render_template('job.html',
                            rein=rein,
                            user=user,
                            order=o,
                            key=key,
                            urls=urls,
                            state=state,
                            found=found,
                            fee=PersistConfig.get(rein, 'fee', 0.00025),
                            unique=unique_documents,
                            job=combined,
                            mediator_fee_btc=mediator_fee_btc)


    @app.route('/mediator')
    def mediator_page():
        Order.update_orders(rein, Document)
        remote_documents = []
        for url in urls:
            sel_url = "{0}query?query=review&owner={1}&testnet={2}&mediator={3}"
            data = safe_get(log, sel_url.format(url, user.maddr, rein.testnet, key))
            if data and 'review' in data:
                remote_documents += filter_and_parse_valid_sigs(rein, data['review'])
        unique_documents = unique(remote_documents)
        job_ids = []
        for doc in unique_documents:
            if 'Job ID' in doc:
                job_ids.append(doc['Job ID'])
        job_ids_string = ','.join(job_ids)

        remote_documents = []
        for url in urls:
            sel_url = "{0}query?owner={1}&query=by_job_id&job_ids={2}&testnet={3}"
            data = safe_get(log, sel_url.format(url, user.maddr, job_ids_string, rein.testnet))
            if data and 'by_job_id' in data:
                remote_documents += filter_and_parse_valid_sigs(rein, data['by_job_id'])
        unique_documents = unique(remote_documents)

        if len(unique_documents) == 0:
            found = False
        else:
            found = True

        return render_template('mediator.html',
                               rein=rein,
                               user=user,
                               key=key,
                               urls=urls,
                               found=found,
                               unique=unique_documents)


    @app.route("/dispute", methods=['POST', 'GET'])
    def job_dispute():
        Order.update_orders(rein, Document)
        form = DisputeForm(request.form)

        our_orders = get_in_process_orders(rein, Document, key, 'Job creator public key', True) + \
                     get_in_process_orders(rein, Document, key, 'Worker public key', True)

        orders = []
        for o in our_orders:
            doc_hash = Document.calc_hash(o['original'])
            d = Document.find(rein, doc_hash, 'remote')
            if d:
                id = d[0].id
            else:
                d = Document(rein, Document.get_document_type(o['original']), o['original'], source_url='remote', testnet=rein.testnet)
                rein.session.add(d)
                rein.session.commit()
                id = d.id

            if o['Job creator public key'] == key:
                role = 'Job creator'
            else:
                role = 'Worker'

            if o['state'] in ['offer', 'delivery', 'creatordispute', 'workerdispute']:
                orders.append((str(id), '{}</td><td>{}'.format( job_link(o),
                                                                role,
                                                              )))

        no_choices = len(orders) == 0

        form.order_id.choices = orders

        if request.method == 'POST' and form.validate_on_submit():
            latest_doc = Document.get(rein, form.order_id.data)
            doc = parse_document(latest_doc.contents)
            fields = [
                {'label': 'Job name',                       'value_from': doc},
                {'label': 'Job ID',                         'value_from': doc},
                {'label': 'Dispute detail',                 'value': form.dispute_detail.data},
                {'label': 'Primary escrow redeem script',   'value_from': doc},
                {'label': 'Mediator escrow redeem script',  'value_from': doc},
                {'label': 'Job creator public key', 'value_from': doc},
                {'label': 'Worker public key', 'value_from':doc},
                {'label': 'Mediator public key', 'value_from':doc}
                     ]

            if key == doc['Job creator public key']:
                title = 'Dispute Delivery'
                doc_type = 'creatordispute'
            else:
                title = 'Dispute Offer'
                doc_type = 'workerdispute'

            document_text = assemble_document(title, fields)
            store = True
            document = sign_and_store_document(rein, doc_type, document_text, user.daddr, user.dkey, store)
            if document and store:
                click.echo("{} created.".format(title))
                sync_core(log, user, key, urls)
                flash("{} signed and pushed to available servers.".format(title))
            assemble_order(rein, document)
            log.info(doc_type + ' signed') if document else log.error(doc_type + ' failed')
            return redirect("/")
        elif request.method == 'POST':
            print("form data " + str(form))
            flash_errors(form)
            return redirect("/dispute")
        else:
            return render_template("dispute.html",
                            form=form,
                            user=user,
                            key=key,
                            urls=urls,
                            block_time=str_block_time,
                            no_choices=no_choices,
                            time_offset=time_offset
                            )


    @app.route("/bid", methods=['POST', 'GET'])
    def job_bid():
        form = BidForm(request.form)

        jobs = []
        for url in urls:
            sel_url = "{0}query?owner={1}&delegate={2}&query=jobs&testnet={3}"
            data = safe_get(log, sel_url.format(url, user.maddr, user.daddr, rein.testnet))
            if data and 'jobs' in data:
                jobs += filter_and_parse_valid_sigs(rein, data['jobs'])

        live_jobs = filter_out_expired(rein, user, urls, jobs)
        unique_jobs = unique(live_jobs, 'Job ID')

        job_ids = []
        for j in unique_jobs:
            order = Order.get_by_job_id(rein, j['Job ID'])
            if not order:
                order = Order(j['Job ID'], testnet=rein.testnet)
                rein.session.add(order)
                rein.session.commit()
            state = order.get_state(rein, Document)

            seconds_left = (int(j['Expiration (days)']) * 86400) - (block_time - int(j['Time']))
            days = int(seconds_left) / 86400
            hours = (seconds_left - days * 86400) / 3600
            time_left = str(days) + 'd ' + str(hours) + 'h'

            if state in ['job_posting', 'bid'] and key not in [j['Job creator public key'], j['Mediator public key']]:
                creator_msin = generate_sin(j['Job creator master address'])
                row = '<a href="http://localhost:'+str(port)+'/job/{}">{}</a></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td><span title="{}">{}</span>'
                job_ids.append((j['Job ID'], row.format(j['Job ID'],
                                                        j['Job name'],
                                                        j['Job creator'],
                                                        get_averave_user_rating_display(log, url, user, rein, creator_msin),
                                                        j['Description'],
                                                        time_left,
                                                        j['Mediator public key'],
                                                        j['Mediator'])))

        no_choices = len(job_ids) == 0

        form.job_id.choices = job_ids

        job = None
        if request.method == 'POST' and form.validate_on_submit():
            job_id = form.job_id.data
            for j in unique_jobs:
                if job_id == j['Job ID']:
                    job = j

            if job is None:
                flash('No matching Job ID found.')
                return redirect("/")

            primary_redeem_script, primary_addr = \
                    build_2_of_3([job['Job creator public key'],
                                  job['Mediator public key'],
                                  key])
            mediator_redeem_script, mediator_escrow_addr = \
                    build_mandatory_multisig(job['Mediator public key'],
                                            [job['Job creator public key'],key])
            fields = [
                {'label': 'Job name',                       'value_from': job},
                {'label': 'Worker',                         'value': user.name},
                {'label': 'Worker contact',                 'value': user.contact},
                {'label': 'Worker delegate address',        'value': user.daddr},
                {'label': 'Worker master address',          'value': user.maddr},
                {'label': 'Description',                    'value': form.description.data},
                {'label': 'Bid amount (BTC)',               'value': form.bid_amount.data},
                {'label': 'Primary escrow address',         'value': primary_addr},
                {'label': 'Mediator escrow address',        'value': mediator_escrow_addr},
                {'label': 'Job ID',                         'value_from': job},
                {'label': 'Job creator',                    'value_from': job},
                {'label': 'Job creator public key',         'value_from': job},
                {'label': 'Mediator public key',            'value_from': job},
                {'label': 'Worker public key',              'value': key},
                {'label': 'Primary escrow redeem script',   'value': primary_redeem_script},
                {'label': 'Mediator escrow redeem script',  'value': mediator_redeem_script},
                     ]
            document_text = assemble_document('Bid', fields)
            store = True
            document = sign_and_store_document(rein, 'bid', document_text, user.daddr, user.dkey, store)
            if document and store:
                click.echo("Bid created.")
                sync_core(log, user, key, urls)
                flash("Bid created and pushed to available servers.")
            assemble_order(rein, document)
            log.info('bid signed') if document else log.error('bid failed')
            return redirect("/")
        elif request.method == 'POST':
            flash_errors(form)
            return redirect("/bid")
        else:
            return render_template("bid.html",
                            form=form,
                            user=user,
                            key=key,
                            urls=urls,
                            documents=documents,
                            orders=orders,
                            jobs=jobs,
                            block_time=str_block_time,
                            no_choices=no_choices,
                            time_offset=time_offset
                            )


    @app.route("/deliver", methods=['POST', 'GET'])
    def job_deliver():
        Order.update_orders(rein, Document)
        form = DeliverForm(request.form)
        key = pubkey(rein.user.dkey)

        jobs = []
        for url in urls:
            sel_url = "{}query?owner={}&delegate={}&worker={}&query=in-process&testnet={}"
            data = safe_get(log, sel_url.format(url, user.maddr, user.daddr, key, rein.testnet))
            if data:
                jobs += filter_and_parse_valid_sigs(rein, data['in-process'])

        unique_jobs = unique(jobs, 'Job ID')

        job_ids = []
        for j in unique_jobs:
            if j['Worker public key'] != key:
                continue

            order = Order.get_by_job_id(rein, j['Job ID'])

            if not order:
                order = Order(j['Job ID'], testnet=rein.testnet)
                rein.session.add(order)
                rein.session.commit()

            state = order.get_state(rein, Document)

            if state in ['offer', 'deliver', 'creatordispute', 'workerdispute']:
                job_ids.append((str(j['Job ID']), job_link(j)))

        no_choices = len(job_ids) == 0

        form.job_id.choices = job_ids

        if request.method == 'POST' and form.validate_on_submit():
            order = Order.get_by_job_id(rein, form.job_id.data)
            offer = order.get_documents(rein, Document, doc_type='offer')
            doc = parse_document(offer[0].contents)
            redeemScript = doc['Primary escrow redeem script']
            mediatorRedeemScript = doc['Mediator escrow redeem script']
            mediator_daddr = str(P2PKHBitcoinAddress.from_pubkey(x(doc['Mediator public key'])))
            try:
                (payment_txins,payment_amount,payment_address,payment_sig) = partial_spend_p2sh(redeemScript,rein)
                (mediator_payment_txins,mediator_payment_amount,mediator_payment_address) = partial_spend_p2sh_mediator(mediatorRedeemScript,rein,mediator_daddr)
            except ValueError as e:
                form.deliverable.errors.append(e.message)
                flash_errors(form)
                return redirect("/deliver")
            fields = [
                {'label': 'Job name',                       'value_from': doc},
                {'label': 'Job ID',                         'value_from': doc},
                {'label': 'Deliverables',                   'value': form.deliverable.data},
                {'label': 'Bid amount (BTC)',               'value_from': doc},
                {'label': 'Primary escrow address',         'value_from': doc},
                {'label': 'Mediator escrow address',        'value_from': doc},
                {'label': 'Primary escrow redeem script',   'value_from': doc},
                {'label': 'Mediator escrow redeem script',  'value_from': doc},
                {'label': 'Worker public key',              'value_from': doc},
                {'label': 'Mediator public key',            'value_from': doc},
                {'label': 'Job creator public key',         'value_from': doc},
                {'label':'Primary payment inputs','value':payment_txins},
                {'label':'Primary payment amount','value':payment_amount},
                {'label':'Primary payment address','value':payment_address},
                {'label':'Primary payment signature','value':payment_sig},
                {'label':'Mediator payment inputs','value':mediator_payment_txins},
                {'label':'Mediator payment amount','value':mediator_payment_amount},
                {'label':'Mediator payment address','value':mediator_payment_address},
                    ]
            document_text = assemble_document('Delivery', fields)
            store = True
            document = sign_and_store_document(rein, 'delivery', document_text, user.daddr, user.dkey, store)
            if document and store:
                click.echo("Delivery created.")
                sync_core(log, user, key, urls)
                flash("Delivery created and pushed to available servers.")
            assemble_order(rein, document)
            log.info('delivery signed') if document else log.error('delivery failed')
            return redirect("/")
        elif request.method == 'POST':
            flash_errors(form)
            return redirect("/deliver")
        else:
            return render_template("deliver.html",
                            form=form,
                            user=user,
                            key=key,
                            urls=urls,
                            documents=documents,
                            orders=orders,
                            bids=bids,
                            block_time=str_block_time,
                            no_choices=no_choices,
                            time_offset=time_offset
                            )


    @app.route('/')
    @app.route('/index.html')
    def serve_template_file():
        documents = Document.get_user_documents(rein)
        Order.update_orders(rein, Document)
        orders = Order.get_user_orders(rein, Document)
        for o in orders:
            setattr(o,'state',STATE[o.get_state(rein, Document)]['past_tense'])
        return render_template('index.html',
                        user=user,
                        key=key,
                        urls=urls,
                        documents=documents,
                        orders=orders)

    webbrowser.open('http://'+host+':' + str(port))
    print("testnet = "+str(rein.testnet))
    app.run(host=host, port=port, debug=rein.debug)

    # testing steps: Disable tor. Then turn on debug because debug doesn't work when socket is overriden


if __name__ == '__main__':
    cli()
