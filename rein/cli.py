import json
import re
import random
import string
import requests
import hashlib
import click
from datetime import datetime
from subprocess import check_output

from sqlalchemy import and_

from lib.ui import create_account, import_account, enroll, identity_prompt
from lib.user import User
from lib.bucket import Bucket, get_bucket_count, create_buckets
from lib.document import Document
from lib.placement import Placement, create_placements
from lib.validate import verify_sig
from lib.bitcoinecdsa import sign, pubkey
from lib.market import mediator_prompt, accept_prompt, job_prompt, bid_prompt, delivery_prompt,\
        creatordispute_prompt, build_document, sign_and_store_document
import lib.config as config

import lib.models

rein = config.Config()


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):
    """
    Rein is a decentralized professional services market. Python-rein is a command-line
    interface to interact with Rein. Use program to create an account, post a job, etc.

\b
    Quick start:
    $ rein setup     - create an identity
    $ rein request   - get free microhosting
    $ rein sync      - push your identity up to your microhosting servers

    For more info visit: http://reinproject.org
    """
    if debug:
        click.echo("Debuggin'")
    pass


@cli.command()
@click.option('--multi/--no-multi', default=False, help="add even if an identity exists")
def setup(multi):
    """
    Setup or import an identity

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
        click.echo("\nWelcome to Rein.\n"
                   "Do you want to import a backup or create a new account?\n\n"
                   "1 - Create new account\n2 - Import backup\n")
        choice = click.prompt("Choice", type=int, default=1)
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
        if res['valid']:
            click.echo("Enrollment complete. Run 'rein request' to request free microhosting to sync to.")
            log.info('enrollment complete')
        else:
            click.echo("Signature verification failed. Please try again.")
            log.error('enrollment failed')
    elif rein.session.query(Document).filter(Document.doc_type == 'enrollment').count() < \
            rein.session.query(User).count():
        click.echo('Continuing previously unfinished setup.')
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
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
def bid(multi, identity):
    """
    Bid on a job.

    Choose from available jobs posted to your registered servers your client knows
    about, and create a bid. Your bid should include the amount of Bitcoin you need
    to complete the job and when you expect to have it complete.
    """
    log = rein.get_log()
    if multi:
        rein.set_multiuser()

    if rein.has_no_account():
        click.echo("Please run setup.")
        return

    user = get_user(rein, identity)

    key = pubkey(user.dkey)
    url = "http://localhost:5000/"
    click.echo("Querying %s for jobs..." % url)
    sel_url = "{0}query?owner={1}&query=jobs"
    answer = requests.get(url=sel_url.format(url, user.maddr))
    data = answer.json()
    if len(data['jobs']) == 0:
        click.echo('None found')

    jobs = filter_valid_sigs(data['jobs'])

    job = job_prompt(rein, jobs)
    if not job:
        return

    log.info('got job for bid')
    document = build_document('Bid',
                              fields=['user', 'key', 'job_name', 'job_id', 'job_creator', 'job_creator_key', 'description', 'amount'],
                              labels=['Worker\'s name',
                                      'Worker\'s public key',
                                      'Job name',
                                      'Job ID',
                                      'Job creator\'s name',
                                      'Job creator\'s public key',
                                      'Description',
                                      'Bid amount (BTC)'],
                              defaults=[user.name, key, job['Job name'], job['Job ID'], job['Job creator\'s name'], job['Job creator\'s public key']]
                              )
    res = sign_and_store_document(rein, 'bid', document, user.daddr, user.dkey)
    if res:
        click.echo("Bid created. Run 'rein sync' to push to available servers.")
    log.info('bid signed') if res else log.error('bid failed')


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
def deliver(multi, identity):
    """
    Deliver on a job.

    Share deliverables with the creator of the job when completed. In the
    event of a dispute, mediators are advised to review the deliverables
    while deciding how to distribute funds.
    """
    log = rein.get_log()
    if multi:
        rein.set_multiuser()

    if rein.has_no_account():
        click.echo("Please run setup.")
        return

    user = get_user(rein, identity)

    key = pubkey(user.dkey)
    url = "http://localhost:5000/"
    click.echo("Querying %s for in-process jobs..." % url)
    sel_url = "{0}query?owner={1}&query=in-process&worker={2}"
    answer = requests.get(url=sel_url.format(url, user.maddr, key))
    results = answer.json()['in-process']
    if len(results) == 0:
        click.echo('None found')

    valid_results = filter_valid_sigs(results, u'Primary escrow redeem script')

    doc = delivery_prompt(rein, valid_results)
    if not doc:
        return

    log.info('got offer for delivery')
    document = build_document('Delivery',
                              fields=['job_id', 'primary_redeem_script', 'mediator_redeem_script', 'deliverables'],
                              labels=['Job ID',
                                      'Primary escrow redeem script',
                                      'Mediator escrow redeem script',
                                      'Deliverables'],
                              defaults=[doc['Job ID'],
                                        doc['Primary escrow redeem script'],
                                        doc['Mediator escrow redeem script']]
                              )
    res = sign_and_store_document(rein, 'delivery', document, user.daddr, user.dkey)
    if res:
        click.echo("Delivery created. Run 'rein sync' to push to available servers.")
    log.info('delivery signed') if res else log.error('delivery failed')


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
def accept(multi, identity):
    """
    Accept a delivery, completing a job.

    Review and accept deliveries for your jobs. Once a delivery is
    accpted, mediators are advised not to sign any tranasctions
    refunding the job creator.
    """
    log = rein.get_log()
    if multi:
        rein.set_multiuser()

    if rein.has_no_account():
        click.echo("Please run setup.")
        return

    user = get_user(rein, identity)

    key = pubkey(user.dkey)
    url = "http://localhost:5000/"
    click.echo("Querying %s for deliveries..." % url)
    # get job ids for jobs for which we've made an offer
    job_ids = []
    offers = rein.session.query(Document).filter(Document.contents.ilike("%Rein Offer%Job creator's public key: "+key+"%")).all()
    for o in offers:
        m = re.search('Job ID: (\S+)', o.contents)
        if m and m.group(1):
            job_ids.append(m.group(1))
    valid_results = []
    for job_id in job_ids:
        sel_url = "{0}query?owner={1}&job_ids={2}&query=delivery"
        answer = requests.get(url=sel_url.format(url, user.maddr, job_id))
        results = answer.json()
        if 'delivery' in results.keys():
            results = results['delivery']
        else:
            continue
        valid_results += filter_valid_sigs(results, u'Primary escrow redeem script')

    if len(valid_results) == 0:
        click.echo('None found')

    doc = accept_prompt(rein, valid_results, "Deliverables")
    if not doc:
        return

    log.info('got delivery for accept')
    document = build_document('Accept Delivery',
                              fields=['job_id', 'primary_redeem_script', 'mediator_redeem_script',
                                      'primary_payment', 'mediator_payment'],
                              labels=['Job ID',
                                      'Primary escrow redeem script',
                                      'Mediator escrow redeem script',
                                      'Signed primary escrow payment',
                                      'Signed mediator escrow payment'],
                              defaults=[doc['Job ID'],
                                        doc['Primary escrow redeem script'],
                                        doc['Mediator escrow redeem script']],
                              )
    res = sign_and_store_document(rein, 'accept', document, user.daddr, user.dkey)
    if res:
        click.echo("Accepted delivery. Run 'rein sync' to push to available servers.")
    log.info('accept signed') if res else log.error('accept failed')


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
def creatordispute(multi, identity):
    """
    Dispute a delivery, triggering mediation.

    If you are a job creator, file a dispute on one of your jobs, for example
    because the job is not done on time, they would use this command to file
    a dispute.
    """
    log = rein.get_log()
    if multi:
        rein.set_multiuser()

    if rein.has_no_account():
        click.echo("Please run setup.")
        return

    user = get_user(rein, identity)

    key = pubkey(user.dkey)
    url = "http://localhost:5000/"
    click.echo("Querying %s for deliveries..." % url)
    # get job ids for jobs for which we've made an offer
    job_ids = []
    offers = rein.session.query(Document).filter(Document.contents.ilike("%Rein Offer%Job creator's public key: "+key+"%")).all()
    for o in offers:
        m = re.search('Job ID: (\S+)', o.contents)
        if m and m.group(1):
            job_ids.append(m.group(1))
    valid_results = []
    fails = 0
    for job_id in job_ids:
        sel_url = "{0}query?owner={1}&job_ids={2}&query=delivery"
        answer = requests.get(url=sel_url.format(url, user.maddr, job_id))
        results = answer.json()
        if 'delivery' in results.keys():
            results = results['delivery']
        else:
            continue
        valid_results += filter_valid_sigs(results, u'Primary escrow redeem script')

    if len(valid_results) == 0:
        click.echo('None found')

    doc = creatordispute_prompt(rein, valid_results, "Deliverables")
    if not doc:
        return

    log.info('got delivery for dispute')
    document = build_document('Dispute Delivery',
                              fields=['job_id', 'primary_redeem_script', 'mediator_redeem_script',
                                      'detail' ,'primary_payment', 'mediator_payment'],
                              labels=['Job ID',
                                      'Primary escrow redeem script',
                                      'Mediator escrow redeem script',
                                      'Dispute detail',
                                      'Signed primary escrow payment',
                                      'Signed mediator escrow payment',
                                      ],
                              defaults=[doc['Job ID'],
                                        doc['Primary escrow redeem script'],
                                        doc['Mediator escrow redeem script']],
                              )
    res = sign_and_store_document(rein, 'creatordispute', document, user.daddr, user.dkey)
    if res:
        click.echo("Dispute signed by job creator. Run 'rein sync' to push to available servers.")
    log.info('creatordispute signed') if res else log.error('creatordispute failed')

@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
def workerdispute(multi, identity):
    """
    Dispute a job, triggering mediation.

    If you are a worker, file a dispute because the creator is
    unresponsive or does not accept work that fulfills the job
    specification, they would use this command to file a dispute.
    """
    log = rein.get_log()
    if multi:
        rein.set_multiuser()

    if rein.has_no_account():
        click.echo("Please run setup.")
        return

    user = get_user(rein, identity)

    key = pubkey(user.dkey)
    url = "http://localhost:5000/"
    click.echo("Querying %s for offers to you..." % url)
    valid_results = []
    fails = 0
    sel_url = "{0}query?owner={1}&worker={2}&query=in-process"
    answer = requests.get(url=sel_url.format(url, user.maddr, key))
    #click.echo(answer.text)
    results = answer.json()
    valid_results += filter_valid_sigs(results['in-process'], u'Primary escrow redeem script')

    if len(valid_results) == 0:
        click.echo('None found')

    doc = creatordispute_prompt(rein, valid_results)
    if not doc:
        return

    log.info('got in-process job for dispute')
    document = build_document('Dispute Offer',
                              fields=['job_id', 'primary_redeem_script', 'mediator_redeem_script',
                                      'detail' ,'primary_payment', 'mediator_payment'],
                              labels=['Job ID',
                                      'Primary escrow redeem script',
                                      'Mediator escrow redeem script',
                                      'Dispute detail',
                                      'Signed primary escrow payment',
                                      'Signed mediator escrow payment'],
                              defaults=[doc['Job ID'],
                                        doc['Primary escrow redeem script'],
                                        doc['Mediator escrow redeem script']],
                              )
    res = sign_and_store_document(rein, 'workerdispute', document, user.daddr, user.dkey)
    if res:
        click.echo("Dispute signed by worker. Run 'rein sync' to push to available servers.")
    log.info('workerdispute signed') if res else log.error('workerdispute failed')


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
def offer(multi, identity):
    """
    Offer - award a bid.

    A job creator would use this command to award the job to a specific bid. 
    Once signed and pushed, escrow addresses should be funded and work can
    begin.
    """
    log = rein.get_log()
    if multi:
        rein.set_multiuser()

    if rein.has_no_account():
        click.echo("Please run setup.")
        return

    user = get_user(rein, identity)

    key = pubkey(user.dkey)
    url = "http://localhost:5000/"
    click.echo("Querying %s for bids on your jobs..." % url)
    sel_url = "{0}query?owner={1}&delegate={2}&query=bids"
    answer = requests.get(url=sel_url.format(url, user.maddr, user.daddr))
    data = answer.json()
    if len(data['bids']) == 0:
        click.echo('None found')

    bids = filter_valid_sigs(data['bids'], u'Primary escrow redeem script')

    bid = bid_prompt(rein, bids)
    if not bid:
        click.echo('None chosen')
        return

    log.info('got bid to offer')
    document = build_document('Offer',
                              fields=['user', 'key',
                                      'worker', 'worker_key',
                                      'mediator', 'mediator_key',
                                      'mediator_escrow_address', 'mediator_escrow_redeem',
                                      'primary_escrow_address', 'primary_escrow_redeem',
                                      'description', 'amount'],
                              labels=['Job name', 'Job creator\'s name', 'Job creator\'s public key',
                                      'Worker\'s name', 'Worker\'s public key',
                                      'Mediator\'s name', 'Mediator\'s public key',
                                      'Mediator escrow address', 'Mediator escrow redeem script',
                                      'Primary escrow address', 'Primary escrow redeem script',
                                      'Description', 'Bid amount (BTC)'],
                              defaults=[bid['Job name'], user.name, key,
                                        bid['Worker\'s name'], bid['Worker\'s public key'],
                                        bid['Job creator\'s name'], bid['Job creator\'s public key']], guid=bid['Job ID'])
    res = sign_and_store_document(rein, 'offer', document, user.daddr, user.dkey)
    if res:
        click.echo("Offer created. Run 'rein sync' to push to available servers.")
    log.info('offer signed') if res else log.error('offer failed')


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
def post(multi, identity):
    """
    Post a job.
    """
    log = rein.get_log()
    if multi:
        rein.set_multiuser()

    if rein.has_no_account():
        click.echo("Please run setup.")
        return

    user = get_user(rein, identity)

    key = pubkey(user.dkey)
    url = "http://localhost:5000/"
    click.echo("Querying %s for mediators..." % url)
    sel_url = "{0}query?owner={1}&query=mediators"
    answer = requests.get(url=sel_url.format(url, user.maddr))
    data = answer.json()
    if len(data['mediators']) == 0:
        click.echo('None found')
    eligible_mediators = filter_valid_sigs(data['mediators'])

    mediator = mediator_prompt(rein, eligible_mediators)
    click.echo("Chosen mediator: " + str(mediator))

    log.info('got user and key for post')
    job_guid = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(20))
    document = build_document('Job',
                              fields=['user', 'key', 'mediator', 'mediator_key', 'name', 'category', 'description'],
                              labels=['Job creator\'s name', 'Job creator\'s public key', # TODO: add contact
                                      'Mediator\'s name', 'Mediator\'s public key',
                                      'Job name', 'Category', 'Description'],
                              defaults=[user.name, key,
                                        mediator['User'], mediator['Mediator pubkey']],
                              guid=job_guid
                              )
    res = sign_and_store_document(rein, 'job_posting', document, user.daddr, user.dkey)
    if res:
        click.echo("Posting created. Run 'rein sync' to push to available servers.")
    log.info('posting signed') if res else log.error('posting failed')


@cli.command()
@click.option('--multi/--no-multi', default=False, help="prompt for identity to use")
@click.option('--identity', type=click.Choice(['Alice', 'Bob', 'Charlie', 'Dan']), default=None, help="identity to use")
@click.argument('url', required=True)
def request(multi, identity, url):
    """
    Request free microhosting space

    During the alpha testing phase, reinproject.org will operate
    at least one free microhosting server. The goal is to incentivize
    a paid network of reliable microhosting servers to store and serve
    all data required for Rein to operate.
    """
    log = rein.get_log()
    if multi:
        rein.set_multiuser()

    user = get_user(rein, identity)

    if rein.has_no_account():
        click.echo("Please run setup.")
        return

    click.echo("User: " + user.name)
    log.info('got user for request')

    if not url.endswith('/'):
        url = url + '/'
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url
    create_buckets(rein.engine)

    if get_bucket_count(rein, url) > 4:
        click.echo("You already have enough (5) buckets from %s" % url)
        log.warning('too many buckets')
        return
    sel_url = "{0}request?owner={1}&delegate={2}&contact={3}"

    try:
        answer = requests.get(url=sel_url.format(url, user.maddr, user.daddr, user.contact))
    except:
        click.echo('Error connecting to server.')
        log.error('server connect error')
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
        b = rein.session.query(Bucket).filter_by(url=url).filter_by(date_created=bucket['created']).first()
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
    Upload records to each registered server

    Each user, bid, offer, etc. (i.e. anything except actual payments) is 
    stored as document across a public database that is maintained across
    a network of paid servers. This command pushes the documents you have
    created to the servers from which you have purchased hosting. 
    """
    log = rein.get_log()
    if multi:
        rein.set_multiuser()

    user = get_user(rein, identity)

    if rein.has_no_account():
        click.echo("Please run setup.")
        return

    click.echo("User: " + user.name)

    create_placements(rein.engine)
    url = "http://localhost:5000/"
    sel_url = url + 'nonce?address={0}'
    answer = requests.get(url=sel_url.format(user.maddr))
    data = answer.json()
    nonce = data['nonce']
    log.info('server returned nonce %s' % nonce)

    check = []
    documents = rein.session.query(Document).filter(Document.identity == user.id).all()
    for doc in documents:
        check.append(doc)
    if len(check) == 0:
        click.echo("Nothing to do.")
    # now that we know what we need to check and upload let's do the checking first, any that
    # come back wrong can be added to the upload queue.
    # download each value (later a hash only with some full downloads for verification)
    upload = []
    verified = []
    for doc in check:
        if len(doc.contents) > 8192:
            click.echo('Document is too big. 8192 bytes should be enough for anyone.')
            log.error("Document oversized %s" % doc.doc_hash)
        else:
            placements = rein.session.query(Placement).filter(and_(Placement.url == url,
                                                                   Placement.doc_id == doc.id)).all()
            if len(placements) == 0:
                upload.append([doc, url])
            else:
                for plc in placements:
                    sel_url = "{0}get?key={1}"
                    answer = requests.get(url=sel_url.format(url, plc.remote_key))
                    data = answer.json()
                    if answer.status_code == 404:
                        log.error("%s not found at %s" % (doc.doc_hash, url))
                        click.echo("document not found")
                        upload.append([doc, url])
                    else:
                        value = data['value']
                        value = value.decode('ascii')
                        value = value.encode('utf8')
                        remote_hash = hashlib.sha256(value).hexdigest()
                        if remote_hash != doc.doc_hash:
                            log.error("%s %s incorrect hash %s != %s " % (url, doc.id, remote_hash, doc.doc_hash))
                            upload.append([doc, url])
                        else:
                            verified.append(doc)

    failed = []
    succeeded = 0
    for doc, url in upload:
        placement = rein.session.query(Placement).filter_by(url=url).filter_by(doc_id=doc.id).all()
        if len(placement) == 0:
            remote_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits)
                                 for _ in range(32))
            plc = Placement(doc.id, url, remote_key)
            rein.session.add(plc)
            rein.session.commit()
        else:
            plc = placement[0]
            for p in placement[1:]:
                rein.session.delete(p)
                rein.session.commit()

        if len(doc.contents) > 8192:
            log.error("Document oversized %s" % doc.doc_hash)
            click.echo('Document is too big. 8192 bytes should be enough for anyone.')
        else:
            message = plc.remote_key + doc.contents + user.daddr + nonce
            message = message.decode('utf8')
            message = message.encode('ascii')
            signature = sign(user.dkey, message)
            data = {"key": plc.remote_key,
                    "value": doc.contents,
                    "nonce": nonce,
                    "signature": signature,
                    "signature_address": user.daddr,
                    "owner": user.maddr}
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

    sel_url = url + 'nonce?address={0}&clear={1}'
    answer = requests.get(url=sel_url.format(user.maddr, nonce))
    log.info('nonce cleared for %s' % (url))
    click.echo('%s docs checked, %s uploaded.' % (len(check), str(succeeded)))


@cli.command()
def upload():
    """
    Do initial share to many servers.
    """
    servers = ['http://bitcoinexchangerate.org/causeway']
    for server in servers:
        url = '%s%s' % (server, '/info.json')
        text = check_output('curl', url)
        try:
            data = json.loads(text)
        except:
            raise RuntimeError('Problem contacting server %s' % server)

        click.echo('%s - %s BTC' % (server, data['price']))


def filter_valid_sigs(docs, expected_field=None):
    valid = []
    fails = 0
    for m in docs:
        data = verify_sig(m)
        if expected_field:
            if data['valid'] and (expected_field in data['info'].keys()):
                valid.append(data['info'])
            else:
                fails += 1
        else:
            if data['valid']:
                valid.append(data['info'])
            else:
                fails += 1
    log.info('spammy fails = %d' % fails)
    return valid


def get_user(rein, identity):
    if rein.multi and identity:
        rein.user = rein.session.query(User).filter(User.name == identity).first()
    elif rein.multi:
        rein.user = identity_prompt(rein)
    else:
        rein.user = rein.session.query(User).first()
    return rein.user
