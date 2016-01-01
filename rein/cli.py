import json
import re
import os
import time
import requests
import click
import sqlite3
from datetime import datetime
from subprocess import check_output

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.user import User, Base, create_account, import_account
from lib.validate import enroll
from lib.bucket import Bucket, create_buckets
import lib.config as config

config_dir = os.path.join(os.path.expanduser('~'), '.rein')
db_filename = 'local.db'

if not os.path.isdir(config_dir):
    os.mkdir(config_dir)

engine = create_engine("sqlite:///%s" % os.path.join(config_dir, db_filename))
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

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
    if not os.path.isfile(db_filename) or session.query(User).count() == 0:
        click.echo("It looks like this is your first time running Rein on this computer.\n"\
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
        res = enroll(user)
        if res['valid']:
            if click.confirm("Signature verified. Would you like to choose some microhosting servers?"):
                upload()
            else:
                click.echo("Signature stored. Run 'rein --upload' to continue with upload to microhosting.")
    else:
        bold = '\033[1m'
        regular = '\033[0m'
        click.echo("""Available commands:

    info, sync, post-job, post-listing, post-bid, post-offer, accept-bid, post-work, accept-work

For more info visit http://reinproject.org
                """)


@cli.command()
@click.argument('url', required=True)
def request(url):
    """
    Request free microhosting space
    """
    if url[-1] != '/':
        url = url + '/'
    if not re.match('/https?:\/\//', url):
        url = 'http://' + url
    user = session.query(User).first()
    
    create_buckets(engine)
    if len(session.query(Bucket).filter_by(url=url).all()) > 5:
        click.echo("Too many buckets.")
        return

    primary_address = user.maddr
    sel_url = "{0}request?address={1}&contact={2}"
    answer = requests.get(url=sel_url.format(url, user.maddr, user.contact))
    if answer.status_code != 200:
        print("Request failed.")
    else:
        data = json.loads(answer.text)

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

    check = []
    upload = []
    succeeded = []
    failed = []
    verified = []

    listing = glob.glob(os.path.join(args.path, "*.json"))
    for l in listing:  
        # check if file is in local key db
        row = con.execute("select * from files where filename = ?", (l,))
        filehash = hashlib.sha256(open(l, 'r').read()).hexdigest()
        if row is None:
            con.execute("insert into files (filename, filehash) VALUES (?, ?)", (l,filehash))
            # for new files, we'll upload them
            upload.append({'name': l})
        else:
            # for existing files, download and verify them
            check.append({'name':row['filename'], 'filehash':row['filehash']})

    # now that we know what we need to check and upload let's do the checking first, any that 
    # come back wrong can be added to the upload queue.
    # download each value (later a hash only with some full downloads for verification)
    for f in check:
        value = open(f['name'], 'r')
        data = value.read()
        value.close()
        if len(data) > 8192:
            raise ValueError('File is too big. 8192 bytes should be enough for anyone.')
        else:
            # handle changes on our side, to update or replace local files?
            row = con.execute("select * from placement inner join files on files.filename = placement.filename\
                                    where placement.filename = ?", (f['name']))
            if row is None:
                upload.append({'name': l})
            else:
                for r in row:
                    # download value, hash and check its hash
                    remote_name = row['remote_filename']
                    sel_url = "{0}get?key={1}"
                    answer = requests.get(url=sel_url.format(args.url, remote_filename))
                    filehash = hashlib.sha256(answer.text).hexdigest()
                    if status_code == 404: 
                        # log not found error in db, add to upload
                        log(f['name'], args.url, "key not found")
                        upload.append(f['name'])
                    elif filehash != r['filehash']:
                        # log wrong error, add to upload
                        upload.append(f['name'])
                        log(f['name'], args.url, "incorrect hash")
                    else:
                        #update verified
                        verified.append(f['name'])

    failed = []
    succeeded = []
    for f in upload:
        value = open(f['name'], 'r')
        data = value.read()
        value.close()
        remote_filename = ''.join(random.SystemRandom().choice(string.ascii_uppercase \
                                + string.digits) for _ in range(32))

        if len(data) > 8192:
            raise ValueError('File is too big. 8192 bytes should be enough for anyone.')
        else:
            a = ''
            setattr(a, 'key', remote_filename)
            setattr(a, 'value', data)
            setattr(a, 'nonce', args.nonce)
            res = json.loads(put(a))
            if 'result' not in res or res['result'] != 'success':
                # houston we have a problem
                log(f['name'], args.url, 'upload failed')
                failed.append(f['name'])
            else:
                succeeded.append({'name': f['name'], 'remote_filename': remote_filename})
                log(f['name'], args.url, 'upload succeeded')

    for f in succeeded:
        row = con.execute("select * from placement where filename = ?", (l,))
        if row is None:
            con.execute("insert into placement (filename, remote_filename, url) values (?, ?)", \
                            (f['name'], f['remote_filename'], args.url))
    

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

