import sys
import json
import re
import random
import string
import requests
import hashlib
import click
from pprint import pprint
from datetime import datetime
from subprocess import check_output

from sqlalchemy import and_

from lib.ui import create_account, import_account, enroll, identity_prompt, hilight
from lib.user import User
from lib.bucket import Bucket
from lib.document import Document, get_user_documents, get_job_id
from lib.placement import Placement, create_placements, get_remote_document_hash, get_placements
from lib.validate import filter_and_parse_valid_sigs, parse_document 
from lib.bitcoinecdsa import sign, pubkey
from lib.market import * 
from lib.order import Order
from lib.script import build_2_of_3, build_mandatory_multisig, check_redeem_scripts
from lib.persistconfig import PersistConfig
import lib.config as config
import lib.models

rein = config.Config()

# TODO: break out store from sign_and_store because dry-run.

@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):
    """
    Rein is a decentralized professional services market. Python-rein is a command-line
interface to interact with Rein. Use this program to create an account, post a job, etc.

\b
    Quick start:
        $ rein setup     - create an identity
        $ rein request   - get free microhosting
        $ rein sync      - push your identity to microhosting servers
        $ rein status    - get user status, or dump of job's documents

\b
    Workers
        $ rein bid       - view and bid on jobs
        $ rein deliver   - complete job by providing deliverables

\b
    Job creators
        $ rein post      - post a job
        $ rein offer     - accept a bid
        $ rein accept    - accept deliverables

\b
    Disputes
        $ rein workerdispute    - worker files dispute
        $ rein creatordispute   - job creator files dispute
        $ rein resolve          - mediator posts decision

    For more info visit: http://reinproject.org
    """
    if debug:
        click.echo("Debuggin'")
    pass


@cli.command()
@click.option('--multi/--no-multi', default=False, help="add even if an identity exists")
def setup(multi):
    """
    Setup or import an identity.

    You will choose a name or handle for your account, include public contact information, 
    and a delegate Bitcoin address/private key that the program will use to sign documents
    on your behalf. An enrollment document will be creatd and you will need to sign it
    with your master Bitcoin private key.
    """
    log = rein.get_log()
    if multi:
        rein.set_multiuser()
    log.info('entering setup')
    if multi or rein.has_no_account():
        click.echo("\n" + hilight("Welcome to Rein.", True, True) + "\n\n"
                   "Do you want to import a backup or create a new account?\n\n"
                   "1 - Create new account\n2 - Import backup\n")
        choice = click.prompt(hilight("Choice", True, True), type=int, default=1)
        if choice == 1:
            create_account(rein)
            log.info('account created')
        elif choice == 2:
            import_account(rein)
            log.info('account imported')
        else:
            click.echo('Invalid choice')
            return
        click.echo("------------")
        click.echo("The file %s has just been saved with your user details and needs to be signed "
                   "with your master Bitcoin private key. The private key for this address should be "
                   "kept offline and multiple encrypted backups made. This key will effectively "
                   "become your identity in Rein and a delegate address will be used for day-to-day "
                   "transactions.\n\n" % rein.enroll_filename)
        res = enroll(rein)
        if isinstance(res, dict) and  res['valid']:
            click.echo("Enrollment complete. Run 'rein request' to request free microhosting to sync to.")
            log.info('enrollment complete')
        else:
            click.echo("Signature verification failed. Please try again.")
            log.error('enrollment failed')
    elif rein.session.query(Document).filter(Document.doc_type == 'enrollment').count() < \
            rein.session.query(User).filter(User.enrolled == True).count():
        click.echo('Continuing previously unfinished setup.\n')
        get_user(rein, False)
        res = enroll(rein)
        if res['valid']:
            click.echo("Enrollment complete. Run 'rein request' to request free microhosting to sync to.")
            log.info('enrollment complete')
        else:
            click.echo("Signature verification failed. Please try again.")
            log.error('enrollment failed')
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
    for url in urls:
        log.info("Querying %s for mediators..." % url)
        sel_url = "{0}query?owner={1}&query=mediators&testnet={2}"
        try:
            answer = requests.get(url=sel_url.format(url, user.maddr, rein.testnet))
        except:
            click.echo('Error connecting to server.')
            log.error('server connect error ' + url)
            continue
        data = answer.json()
        if len(data['mediators']) == 0:
            click.echo('None found')
        eligible_mediators += filter_and_parse_valid_sigs(rein, data['mediators'])

    if 'Mediator public key' in form.keys():
        mediator = select_by_form(eligible_mediators, 'Mediator public key', form)
    else:
        click.echo("Post a job\n\nFunds for each job in Rein are stored in two multisig addresses. One address\n"
                   "is for the primary payment that will go to the worker on completion. The\n"
                   "second address pays the mediator to be available to resolve a dispute whether\n"
                   "if necessary. The second address should be funded according to the percentage\n"
                   "specified by the mediator and is in addition to the primary payment. The\n"
                   "listing below shows available mediators and the fee they charge. You should\n"
                   "consider the fee as well as any reputational data you are able to find when\n"
                   "choosing a mediator. You choice may affect the number and quality of bids\n"
                   "you receive.\n")
        mediator = mediator_prompt(rein, eligible_mediators)
    if not mediator:
        return
    click.echo("Chosen mediator: " + str(mediator['User']))

    log.info('got user and key for post')
    job_guid = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(20))
    fields = [
                {'label': 'Job name',                       'not_null': form},
                {'label': 'Job ID',                         'value': job_guid},
                {'label': 'Category',                       'not_null': form},
                {'label': 'Description',                    'not_null': form},
                {'label': 'Mediator',                       'value': mediator['User']},
                {'label': 'Mediator contact',               'value': mediator['Contact']},
                {'label': 'Mediator fee',                   'value': mediator['Mediator fee']},
                {'label': 'Mediator public key',            'value': mediator['Mediator public key']},
                {'label': 'Mediator master address',        'value': mediator['Master signing address']},
                {'label': 'Job creator',                    'value': user.name},
                {'label': 'Job creator contact',            'value': user.contact},
                {'label': 'Job creator public key',         'value': key},
                {'label': 'Job creator master address',     'value': user.maddr},
             ]
    document_text = assemble_document('Job', fields)
    if not rein.testnet:
        m = re.search('test', document_text, re.IGNORECASE)
        if m:
            click.echo('Your post includes the word "test". If this post is a test, '
                       'please put rein into testnet mode with "rein testnet true" '
                       'and setup a test identity before posting.')
            if not click.confirm(hilight('Would you like to continue to post this on mainnet?', True, True), default=False):
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

    Choose from available jobs posted to your registered servers your client knows
    about, and create a bid. Your bid should include the amount of Bitcoin you need
    to complete the job and when you expect to have it complete.
    """
    
    (log, user, key, urls) = init(multi, identity)
    form = {}
    if defaults:
        form = parse_document(open(defaults).read())
        if 'Title' in form and form['Title'] != 'Rein Bid':
            return click.echo("Input file type: " + form['Title'])
    store = False if dry_run else True

    jobs = []
    for url in urls:    
        log.info("Querying %s for jobs..." % url)
        sel_url = "{0}query?owner={1}&query=jobs&testnet={2}"
        try:
            answer = requests.get(url=sel_url.format(url, user.maddr, rein.testnet))
        except:
            click.echo('Error connecting to server.')
            log.error('server connect error ' + url)
            continue
        data = answer.json()
        jobs += filter_and_parse_valid_sigs(rein, data['jobs'])

    unique_jobs = unique(jobs, 'Job ID')

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
                {'label': 'Worker contacat',                'value': user.contact},
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
    Once signed and pushed, escrow addresses should be funded and work can
    begin.
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
        log.info("Querying %s for bids on your jobs..." % url)
        sel_url = "{0}query?owner={1}&delegate={2}&query=bids&testnet={3}"
        try:
            answer = requests.get(url=sel_url.format(url, user.maddr, user.daddr, rein.testnet))
        except:
            click.echo('Error connecting to server.')
            log.error('server connect error ' + url)
            continue
        data = answer.json()
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

    Order.update_orders(rein, Document, get_user_documents)

    documents = []
    orders = Order.get_user_orders(rein, Document)
    for order in orders:
        state = order.get_state(rein, Document)
        if state in ['offer', 'delivery']:
            # get parsed offer for this order and put it in an array
            documents += order.get_documents(rein, Document, state)

    contents = []
    for document in documents:
        contents.append(document.contents)

    offers = filter_and_parse_valid_sigs(rein, contents)

    not_our_orders = []
    for res in offers:
        if res['Job creator public key'] != key:
            not_our_orders.append(res)

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
    fields = [
                {'label': 'Job name',                       'value_from': doc},
                {'label': 'Job ID',                         'value_from': doc},
                {'label': 'Deliverables',                   'not_null': form},
                {'label': 'Bid amount (BTC)',               'value_from': doc},
                {'label': 'Primary escrow address',         'value_from': doc},
                {'label': 'Mediator escrow address',        'value_from': doc},
                {'label': 'Primary escrow redeem script',   'value_from': doc},
                {'label': 'Mediator escrow redeem script',  'value_from': doc},
                {'label': 'Worker public key',              'value_from': doc},
                {'label': 'Mediator public key',            'value_from': doc},
                {'label': 'Job creator public key',         'value_from': doc},
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

    Order.update_orders(rein, Document, get_user_documents)

    documents = []
    orders = Order.get_user_orders(rein, Document)
    for order in orders:
        state = order.get_state(rein, Document)
        if state in ['offer', 'delivery']:
            # get parsed offer for this order and put it in an array
            documents += order.get_documents(rein, Document, state)

    contents = []
    for document in documents:
        contents.append(document.contents)

    valid_results = filter_and_parse_valid_sigs(rein, contents)

    our_orders = []
    for res in valid_results:
        if res['Job creator public key'] == key:
            order = Order.get_by_job_id(rein, res['Job ID'])
            res['state'] = order.get_state(rein, Document)
            our_orders.append(res)

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

    fields = [
                {'label': 'Job name',                       'value_from': doc},
                {'label': 'Job ID',                         'value_from': doc},
                {'label': 'Signed primary payment',         'not_null': form},
                {'label': 'Signed mediator payment',        'not_null': form},
                {'label': 'Primary escrow redeem script',   'value_from': doc},
                {'label': 'Mediator escrow redeem script',  'value_from': doc},
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

    If you are a job creator, file a dispute on one of your jobs, for example
    because the job is not done on time, they would use this command to file
    a dispute.
    """
    (log, user, key, urls) = init(multi, identity)
    form = {}
    if defaults:
        form = parse_document(open(defaults).read())
        if 'Title' in form and form['Title'] != 'Rein Dispute Delivery':
            return click.echo("Input file type: " + form['Title'])
    store = False if dry_run else True

    Order.update_orders(rein, Document, get_user_documents)

    documents = []
    orders = Order.get_user_orders(rein, Document)
    for order in orders:
        state = order.get_state(rein, Document)
        if state in ['offer', 'delivery']:
            # get parsed offer for this order and put it in an array
            documents += order.get_documents(rein, Document, state)

    contents = []
    for document in documents:
        contents.append(document.contents)

    valid_results = filter_and_parse_valid_sigs(rein, contents)

    if len(valid_results) == 0:
        click.echo('None found')
        return

    if 'Job ID' in form.keys():
        doc = select_by_form(valid_results, 'Job ID', form)
    else:
        doc = dispute_prompt(rein, valid_results, "Deliverables")
    if not doc:
        return

    log.info('got delivery for dispute')
    fields = [
                {'label': 'Job name',                       'value_from': doc},
                {'label': 'Job ID',                         'value_from': doc},
                {'label': 'Dispute detail',                 'not_null': form},
                {'label': 'Primary escrow redeem script',   'value_from': doc},
                {'label': 'Mediator escrow redeem script',  'value_from': doc},
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

    valid_results = []

    Order.update_orders(rein, Document, get_user_documents)

    documents = []
    orders = Order.get_user_orders(rein, Document)
    for order in orders:
        state = order.get_state(rein, Document)
        if state in ['offer', 'delivery']:
            # get parsed offer for this order and put it in an array
            documents += order.get_documents(rein, Document, state)

    contents = []
    for document in documents:
        contents.append(document.contents)

    valid_results = filter_and_parse_valid_sigs(rein, contents)
    
    if len(valid_results) == 0:
        click.echo('None found')
        return

    if 'Job ID' in form.keys():
        doc = select_by_form(valid_results, 'Job ID', form)
    else:
        doc = dispute_prompt(rein, valid_results, 'Deliverables')
    if not doc:
        return

    log.info('got in-process job for dispute')
    fields = [
                {'label': 'Job name',                       'value_from': doc},
                {'label': 'Job ID',                         'value_from': doc},
                {'label': 'Dispute detail',                 'not_null': form},
                {'label': 'Primary escrow redeem script',   'value_from': doc},
                {'label': 'Mediator escrow redeem script',  'value_from': doc},
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

    For mediators who are party to a disputed transaction, this
    command enables you to review those transactions and post
    the decision and signed payments.
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
        log.info("Querying %s for jobs we're mediating..." % url)
        sel_url = "{0}query?owner={1}&query=review&mediator={2}&testnet={3}"
        try:
            answer = requests.get(url=sel_url.format(url, user.maddr, key, rein.testnet))
        except:
            click.echo('Error connecting to server.')
            log.error('server connect error ' + url)
            continue
        results = answer.json()['review']
        valid_results += filter_and_parse_valid_sigs(rein, results)

    valid_results = unique(valid_results, 'Job ID')

    job_ids = []
    for result in valid_results:
        if 'Job ID' in result and result['Job ID'] not in job_ids:
            job_ids.append(result['Job ID'])

    job_ids_string = ','.join(job_ids)
    valid_results = []
    for url in urls:
        log.info("Querying %s for %s ..." % (url, job_ids_string))
        sel_url = "{0}query?owner={1}&job_ids={2}&query=by_job_id&testnet={3}"
        try:
            answer = requests.get(url=sel_url.format(url, user.maddr, job_ids_string, rein.testnet))
        except:
            click.echo('Error connecting to server.')
            log.error('server connect error ' + url)
            continue
        results = answer.json()
        if 'by_job_id' in results.keys():
            results = results['by_job_id']
        else:
            continue
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
    fields = [
                {'label': 'Job name',                       'value_from': doc},
                {'label': 'Job ID',                         'value_from': doc},
                {'label': 'Resolution',                     'not_null': form},
                {'label': 'Signed primary payment',         'not_null': form},
                {'label': 'Signed mediator payment',        'not_null': form},
             ]
    document = assemble_document('Dispute Resolution', fields)
    res = sign_and_store_document(rein, 'resolve', document, user.daddr, user.dkey, store)
    if res and store:
        click.echo("Dispute resolution signed by mediator. Run 'rein sync' to push to available servers.")
    log.info('resolve signed') if res else log.error('resolve failed')


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
        url = url + '/'
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url

    if Bucket.get_bucket_count(rein, url) > 4:
        click.echo("You already have enough (3) buckets from %s" % url)
        log.warning('too many buckets')
        return
    sel_url = "{0}request?owner={1}&delegate={2}&contact={3}"

    try:
        answer = requests.get(url=sel_url.format(url, user.maddr, user.daddr, user.contact))
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
        b = rein.session.query(Bucket).filter(and_(Bucket.url==url, Bucket.date_created==bucket['created'])).first()
        if b is None:
            b = Bucket(url, user.id, bucket['id'], bucket['bytes_free'],
                       datetime.strptime(bucket['created'], '%Y-%m-%d %H:%M:%S'))
            rein.session.add(b)
            rein.session.commit()
        log.info('saved bucket created %s' % bucket['created'])


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
def sync(multi, identity):
    """
    Upload records to each registered server.

    Each user, bid, offer, etc. (i.e. anything except actual payments) is 
    stored as document across a public database that is maintained across
    a network of paid servers. This command pushes the documents you have
    created to the servers from which you have purchased hosting. 
    """
    (log, user, key, urls) = init(multi, identity)

    click.echo("User: " + user.name)

    if len(urls) == 0:
        click.echo("No buckets registered. Run 'rein request' to continue.")
        return

    create_placements(rein.engine)

    upload = []
    nonce = {}
    for url in urls:
        nonce[url] = get_new_nonce(rein, url)
        if nonce[url] is None:
            continue
        check = get_user_documents(rein) 
        if len(check) == 0:
            click.echo("Nothing to do.")

        for doc in check:
            if len(doc.contents) > 8192:
                click.echo('Document is too big. 8192 bytes should be enough for anyone.')
                log.error("Document oversized %s" % doc.doc_hash)
            else:
                placements = get_placements(rein, url, doc.id)
                           
                if len(placements) == 0:
                    upload.append([doc, url])
                else:
                    for plc in placements:
                        if get_remote_document_hash(rein, plc) != doc.doc_hash:
                            upload.append([doc, url])
    
    failed = []
    succeeded = 0
    for doc, url in upload:
        placements = get_placements(rein, url, doc.id)
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
            answer = requests.post(url='{0}put'.format(url), headers=headers, data=body)
            res = answer.json()
            if 'result' not in res or res['result'] != 'success':
                log.error('upload failed doc=%s plc=%s url=%s' % (doc.id, plc.id, url))
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
        answer = requests.get(url=sel_url.format(user.maddr, nonce[url]))
        log.info('nonce cleared for %s' % (url))

    click.echo('%s docs checked on %s servers, %s uploads done.' % (len(check), len(urls), str(succeeded)))


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.option('--jobid', default=None, help="ID of job, dumps documents to screen")
def status(multi, identity, jobid):
    """
    Show user info and active jobs.
    """
    (log, user, key, urls) = init(multi, identity)

    Order.update_orders(rein, Document, get_user_documents)
    documents = get_user_documents(rein)

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
        click.echo("Testnet: %s" % PersistConfig.get_testnet(rein))
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
            log.info("Querying %s for job id %s..." % (url, jobid))
            sel_url = "{0}query?owner={1}&query=by_job_id&job_ids={2}&testnet={3}"
            try:
                answer = requests.get(url=sel_url.format(url, user.maddr, jobid, rein.testnet))
            except:
                click.echo('Error connecting to server.')
                log.error('server connect error ' + url)
                continue
            data = answer.json()
            remote_documents += filter_and_parse_valid_sigs(rein, data['by_job_id'])
        unique_documents = unique(remote_documents)
        for doc in remote_documents:
            click.echo(doc)
        if len(remote_documents) == 0:
            order = Order.get_by_job_id(rein, jobid)
            if order:
                documents = order.get_documents(rein, Document)
                for document in documents:
                    click.echo("\n" + document.contents)
            else:
                click.echo("Job id not found")

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
        PersistConfig.set_testnet(rein, 'true')
        click.echo("Testnet enabled. Run 'rein testnet false' to go back to mainnet")
    else:
        PersistConfig.set_testnet(rein, 'false')
        click.echo("Testnet disabled. Run 'rein testnet true' to go back to testnet")
    return


def init(multi, identity):
    log = rein.get_log()
    if multi:
        rein.set_multiuser()
    if rein.has_no_account():
        click.echo("Please run setup.")
        return sys.exit(1)
    user = get_user(rein, identity)
    key = pubkey(user.dkey)
    urls = Bucket.get_urls(rein)
    return (log, user, key, urls)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def get_user(rein, identity):
    if rein.multi and identity:
        rein.user = rein.session.query(User).filter(User.name == identity,
                                                    User.enrolled == True,
                                                    User.testnet == rein.testnet).first()
    elif rein.multi:
        rein.user = identity_prompt(rein)
    else:
        rein.user = rein.session.query(User).filter(User.enrolled == True,
                                                    User.testnet == rein.testnet).first()
    return rein.user


def get_new_nonce(rein, url):
    sel_url = url + 'nonce?address={0}'
    try:
        answer = requests.get(url=sel_url.format(rein.user.maddr))
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
