import json
import re
import os
import time
import random
import string
import requests
import hashlib
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
from lib.validate import enroll, validate_enrollment
from lib.bitcoinaddress import check_bitcoin_address 
from lib.bitcoinecdsa import sign, pubkey
from lib.market import create_signed_document

import lib.config as config

config_dir = os.path.join(os.path.expanduser('~'), '.rein')
db_filename = 'local.db'

if not os.path.isdir(config_dir):
    os.mkdir(config_dir)

engine = create_engine("sqlite:///%s" % os.path.join(config_dir, db_filename))
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
Base.metadata.create_all(engine)

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
    click.echo("\nWelcome to Rein.\n")
    if not os.path.isfile(os.path.join(config_dir, db_filename)) or session.query(User).count() == 0:
        click.echo("It looks like this is your first time running Rein.\n"\
                "Do you want to import a backup or create a new account?\n\n"\
                "1 - Create new account\n2 - Import backup\n")
        choice = 0
        user = None
        while choice not in (1, 2):
            choice = click.prompt("Choice", type=int, default=1)
            if choice == 1:
                user = create_account(engine, session)
            elif choice == 2:
                user = import_account(engine, session)
        click.echo("------------")
        click.echo("The file %s has just been saved with your user details and needs to be signed "\
                "with your master Bitcoin private key. The private key for this address should be "\
                "kept offline and multiple encrypted backups made. This key will effectively "\
                "become your identity in Rein and a delegate address will be used for day to day "\
                "transactions.\n\n" % config.enroll_filename)
        res = enroll(session, engine, user)
        if res['valid']:
            click.echo("Enrollment complete. Run 'rein request' to request free microhosting to sync to.")
        else:
            click.echo("Signature verification failed. Please try again.")
    else:
        bold = '\033[1m'
        regular = '\033[0m'
        click.echo("""Identity already setup.

Available commands:

    request, sync, post-job, post-listing, post-bid, post-offer, accept-bid, post-work, accept-work

For more info visit http://reinproject.org
                """)


@cli.command()
def post():
    """
    Post a job.
    """
    user = session.query(User).first()
    key = pubkey(user.dkey)

    create_signed_document(session, "Job", 'job_posting', ['user', 'key', 'name', 'category', 'description'], \
            ['Job creator\'s name', 'Job creator\'s public key', 'Job name', 'Category', 'Description'], \
            [user.name, key], user.daddr, user.dkey)


@cli.command()
@click.argument('url', required=True)
def request(url):
    """
    Request free microhosting space
    """
    if url[-1] != '/':
        url = url + '/'
    if url.find('http://') < 0 and url.find('https://') < 0:
        url = 'http://' + url
    user = session.query(User).first()
    
    create_buckets(engine)
    if len(session.query(Bucket).filter_by(url=url).all()) > 5:
        click.echo("You already have enough buckets from %s" % url)
        return

    sel_url = "{0}request?owner={1}&contact={2}"
    try:
        answer = requests.get(url=sel_url.format(url, user.maddr, user.contact))
    except:
        click.echo('Error connecting to server.')
        return
    if answer.status_code != 200:
        click.echo("Request failed. Please try again later or with a different server.")
        return
    else:
        data = json.loads(answer.text)
    
    if 'result' in data and data['result'] == 'error':
        click.echo('The server returned an error: %s' % data['message'])

    for bucket in data['buckets']:
        b = session.query(Bucket).filter_by(url=url).filter_by(date_created=bucket['created']).first()
        if b is None:
            b = Bucket(url, bucket['id'], bucket['bytes_free'], datetime.strptime(bucket['created'], '%Y-%m-%d %H:%M:%S'))
            session.add(b)
            session.commit()
"""
{
   "buckets": [
      {
          "bytes_free": "1048576",
          "created": "2015-12-31 05:09:38"
      },
   ],
   "result": "success"
}
"""

@cli.command()
def sync():
    """
    Upload records to each registered server
    """ 
    create_placements(engine)

    #for first try hardcode it
    url = "http://localhost:5000/"

    # get new nonce from server
    identity = session.query(User).first()
    sel_url = url + 'nonce?address={0}'
    answer = requests.get(url=sel_url.format(identity.maddr))
    data = answer.json()
    nonce = data['nonce']
    #click.echo('nonce = %s' % nonce)

    check = []
    upload = []
    succeeded = []
    failed = []
    verified = []

    # get list of stored documents
    documents = session.query(Document).all()
    for doc in documents:
        check.append(doc)

    #click.echo("check " + str(check))
    # now that we know what we need to check and upload let's do the checking first, any that 
    # come back wrong can be added to the upload queue.
    # download each value (later a hash only with some full downloads for verification)
    for doc in check:
        if len(doc.contents) > 8192:
            raise ValueError('Document is too big. 8192 bytes should be enough for anyone.')
        else:
            # see if we have a placement for this document already
            placements = session.query(Placement).filter(and_(Placement.url==url, Placement.doc_id==doc.id)).all()
            if len(placements) == 0:
                #click.echo('no existing placement for %s' % doc.doc_hash)
                upload.append(doc)
            else:
                for plc in placements:
                    # download value, hash and check its hash
                    sel_url = "{0}get?key={1}"
                    answer = requests.get(url=sel_url.format(url, plc.remote_key))
                    data = answer.json()
                    value = data['value']
                    value = value.decode('ascii')
                    value = value.encode('utf8')
                    remote_hash = hashlib.sha256(value).hexdigest()
                    if answer.status_code == 404: 
                        # log not found error in db, add to upload
                        #log(doc.id, url, "key not found")
                        click.echo("document not found")
                        upload.append(doc)
                    elif remote_hash != doc.doc_hash:
                        # log wrong error, add to upload
                        #log(doc.id, url, "incorrect hash")
                        click.echo("hash mismatch")
                        upload.append(doc)
                    else:
                        #update verified
                        verified.append(doc)

    #click.echo("upload " + str(upload))
    failed = []
    succeeded = []
    for doc in upload:
        doc.remote_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase \
                                + string.digits) for _ in range(32))

        if len(doc.contents) > 8192:
            raise ValueError('Document is too big. 8192 bytes should be enough for anyone.')
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

            sel_url = "{0}put"
            body = json.dumps(data)
            headers = {'Content-Type': 'application/json'}
            answer = requests.post(url=sel_url.format(url), headers=headers, data=body)
            res = answer.json() 

            if 'result' not in res or res['result'] != 'success':
                # houston we have a problem
                #log(doc.id, url, 'upload failed')
                failed.append(doc)
            else:
                click.echo('uploaded %s' % doc.doc_hash)
                session.commit()
                succeeded.append(doc)
                #log(doc.id, url, 'upload succeeded')

    #click.echo("succeeded " + str(succeeded))
    #click.echo("failed " + str(failed))
    for doc in succeeded:
        placement = session.query(Placement).filter_by(url=url).filter_by(doc_id=doc.id).all()
        if len(placement) == 0:
            p = Placement(doc.id, url, doc.remote_key)
            session.add(p)
            session.commit()
            click.echo('recorded_upload %s' % doc.doc_hash)
    
    # clear nonce
    sel_url = url + 'nonce?address={0}&clear={1}'
    answer = requests.get(url=sel_url.format(identity.maddr, nonce))
    data = answer.json()
    nonce = data['nonce']

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

