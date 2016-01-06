import json
import re
import os
import time
import random
import string
import requests
import hashlib
import logging
import click
import sqlite3
from datetime import datetime
from subprocess import check_output

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

from lib.user import User, Base, create_account, import_account
from lib.bucket import Bucket, create_buckets
from lib.document import Document
from lib.placement import Placement, create_placements
from lib.validate import enroll, validate_enrollment, verify_sig
from lib.bitcoinaddress import check_bitcoin_address 
from lib.bitcoinecdsa import sign, pubkey
from lib.market import create_signed_document

import lib.config as config

log = logging.getLogger('python-rein')
logging.basicConfig(filename="rein.log", filemode="w")
log.setLevel(logging.INFO)

log.info('starting python-rein')

config_dir = os.path.join(os.path.expanduser('~'), '.rein')
db_filename = 'local.db'

if not os.path.isdir(config_dir):
    os.mkdir(config_dir)

engine = create_engine("sqlite:///%s" % os.path.join(config_dir, db_filename))
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
Base.metadata.create_all(engine)
log.info('database connected')

@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):
    if debug:
        click.echo("Debuggin'")
    pass

@cli.command()
def setup():
    """
    Setup or import an identity
    """
    log.info('entering setup')
    if not os.path.isfile(os.path.join(config_dir, db_filename)) or session.query(User).count() == 0:
        click.echo("\nWelcome to Rein.\n"\
                "Do you want to import a backup or create a new account?\n\n"\
                "1 - Create new account\n2 - Import backup\n")
        user = None
        choice = click.prompt("Choice", type=int, default=1)
        if choice == 1:
            user = create_account(engine, session)
            log.info('account created')
        elif choice == 2:
            user = import_account(engine, session)
            log.info('account imported')
        else:
            click.echo('Invalid choice')
            return
        click.echo("------------")
        click.echo("The file %s has just been saved with your user details and needs to be signed "\
                "with your master Bitcoin private key. The private key for this address should be "\
                "kept offline and multiple encrypted backups made. This key will effectively "\
                "become your identity in Rein and a delegate address will be used for day-to-day "\
                "transactions.\n\n" % config.enroll_filename)
        res = enroll(session, engine, user)
        if res['valid']:
            click.echo("Enrollment complete. Run 'rein request' to request free microhosting to sync to.")
            log.info('enrollment complete')
        else:
            click.echo("Signature verification failed. Please try again.")
            log.error('enrollment failed')
    else:
        bold = '\033[1m'
        regular = '\033[0m'
        click.echo("Identity already setup.")
    log.info('exiting setup')


@cli.command()
def post():
    """
    Post a job.
    """
    user = session.query(User).first()
    key = pubkey(user.dkey)
    url = "http://localhost:5000/"
    #query for a mediator
    sel_url = "{0}query?owner={1}&query=mediators"
    answer = requests.get(url=sel_url.format(url, user.maddr))
    data = answer.json()
    for m in data['mediators']:
        click.echo(verify_sig(m))

    # show menu of available mediators
    return
    log.info('got user and key for post')
    res = create_signed_document(session, "Job", 'job_posting',\
            ['user', 'key', 'name', 'category', 'description'],\
            ['Job creator\'s name', 'Job creator\'s public key', 'Job name', 'Category', 'Description'],\
            [user.name, key], user.daddr, user.dkey)
    log.info('posting signed') if res else log.error('posting failed')


@cli.command()
@click.argument('url', required=True)
def request(url):
    """
    Request free microhosting space
    """
    if not url.endswith('/'):
        url = url + '/'
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url
    user = session.query(User).first()
    log.info('got user for request')    
    create_buckets(engine)
    if len(session.query(Bucket).filter_by(url=url).all()) > 4:
        click.echo("You already have enough buckets from %s" % url)
        log.warning('too many buckets')
        return
    sel_url = "{0}request?owner={1}&contact={2}"
    try:
        answer = requests.get(url=sel_url.format(url, user.maddr, user.contact))
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
        log.info('server request successful')
    if 'result' in data and data['result'] == 'error':
        click.echo('The server returned an error: %s' % data['message'])
    for bucket in data['buckets']:
        b = session.query(Bucket).filter_by(url=url).filter_by(date_created=bucket['created']).first()
        if b is None:
            b = Bucket(url, bucket['id'], bucket['bytes_free'], datetime.strptime(bucket['created'], '%Y-%m-%d %H:%M:%S'))
            session.add(b)
            session.commit()
        log.info('saved bucket created %s' % bucket['created'])


@cli.command()
def sync():
    """
    Upload records to each registered server
    """ 
    create_placements(engine)
    url = "http://localhost:5000/"
#identity = session.query(User).first()
#    click.echo(identity)
    sel_url = url + 'nonce?address={0}'
#    answer = requests.get(url=sel_url.format(identity.maddr))
#    data = answer.json()
#    nonce = data['nonce']
    nonce = ''
    log.info('server returned nonce %s' % nonce)

    check = []
    documents = session.query(Document).all()
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
            placements = session.query(Placement).filter(and_(Placement.url==url, Placement.doc_id==doc.id)).all()
            if placements is None:
                upload.append(doc)
            else:
                for plc in placements:
                    sel_url = "{0}get?key={1}"
                    answer = requests.get(url=sel_url.format(url, plc.remote_key))
                    data = answer.json()
                    value = data['value']
                    value = value.decode('ascii')
                    value = value.encode('utf8')
                    remote_hash = hashlib.sha256(value).hexdigest()
                    if answer.status_code == 404: 
                        log("%s not found at %s" % (doc.doc_hash, url))
                        click.echo("document not found")
                        upload.append(doc)
                    elif remote_hash != doc.doc_hash:
                        log("%s incorrect hash at %s" % (doc.id, url))
                        click.echo("hash mismatch")
                        upload.append(doc)
                    else:
                        verified.append(doc)
    
    failed = []
    succeeded = []
    for doc in upload:
        doc.remote_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase \
                                + string.digits) for _ in range(32))
        if len(doc.contents) > 8192:
            log.error("Document oversized %s" % doc.doc_hash)
            click.echo('Document is too big. 8192 bytes should be enough for anyone.')
        else:
            message = doc.remote_key + doc.contents + identity.daddr + nonce
            message = message.decode('utf8')
            message = message.encode('ascii')
            signature = sign(identity.dkey, message)
            data = {"key": doc.remote_key,
                    "value": doc.contents,
                    "nonce": nonce,
                    "signature": signature,
                    "signature_address": identity.daddr,
                    "owner": identity.maddr}
            body = json.dumps(data)
            headers = {'Content-Type': 'application/json'}
            answer = requests.post(url='{0}put'.format(url), headers=headers, data=body)
            res = answer.json() 
            if 'result' not in res or res['result'] != 'success':
                log.error('upload failed %s %s' % (doc.id, url))
                failed.append(doc)
            else:
                session.commit()
                succeeded.append(doc)
                log.info('upload succeeded %s %s' % (doc.id, url))
                click.echo('uploaded %s' % doc.doc_hash)

    for doc in succeeded:
        placement = session.query(Placement).filter_by(url=url).filter_by(doc_id=doc.id).all()
        if placement is None:
            p = Placement(doc.id, url, doc.remote_key)
            session.add(p)
            session.commit()
            log.info('upload succeeded %s %s' % (doc.id, url))
    
    sel_url = url + 'nonce?address={0}&clear={1}'
    answer = requests.get(url=sel_url.format(identity.maddr, nonce))
    log.info('nonce cleared for %s' % (url))
    click.echo('%s docs checked, %s uploaded.' % (len(check),len(succeeded)))

@cli.command()
def upload():
    """
    Do initial share to many servers.
    """
    servers = ['http://bitcoinexchangerate.org/causeway']
    for server in servers:
        url = '%s%s' % (server, '/info.json')
        text = check_output('curl',url)
        try:
            data = json.loads(text)
        except:
            raise RuntimeError('Problem contacting server %s' % server)

        click.echo('%s - %s BTC' % (server, data['price']))

