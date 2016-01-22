import hashlib
import requests
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from order import Order

Base = declarative_base()


class Document(Base):
    __tablename__ = 'document'

    id = Column(Integer, primary_key=True)
    identity = Column(Integer, nullable=False)
    doc_type = Column(String(64), nullable=True)
    doc_hash = Column(String(250), nullable=False)
    contents = Column(String(8192), nullable=False)
    source_url = Column(String(250), nullable=False)
    source_key = Column(String(64), nullable=True)
    sig_verified = Column(Integer, default=False)
    order_id = Column(Integer, ForeignKey(Order.id))

    def __init__(self, rein, doc_type, contents, source_url='local',
                 source_key=None, sig_verified=False):
        self.identity = rein.user.id
        self.doc_type = doc_type  # enrollment, bid, offer, job, for_hire,
        self.doc_hash = hashlib.sha256(contents).hexdigest()
        self.contents = contents
        self.source_url = source_url
        self.source_key = source_key
        self.sig_verified = sig_verified

    def get_hash(self):
        return self.doc_hash

    def set_order_id(self, id):
        self.order_id = id


def get_user_documents(rein):
    return rein.session.query(Document).filter(Document.identity == rein.user.id).all()


def get_documents_by_job_id(rein, url, job_id):
    click.echo("Querying %s for jobs with job_id %s ..." % (url, job_id))
    sel_url = "{0}query?owner={1}&query=by_job_id&job_ids={2}"
    answer = requests.get(url=sel_url.format(url, rein.user.maddr, job_id))
    data = answer.json()
    if len(data['documents']) == 0:
        click.echo('None found')
    return filter_valid_sigs(data['documents'])

def get_job_id(text):
    m = re.search('Job ID: (.+)\n', text)
    if m:
        return m.group(1)
    else:
        return None

def get_doc_type(text):
    titles = [{'Rein User Enrollment':    'enrollment'},
              {'Rein Job':                'job_posting'},
              {'Rein Bid':                'bid'},
              {'Rein Offer':              'offer'},
              {'Rein Delivery':           'delivery'},
              {'Rein Accept Delivery':    'accept'},
              {'Rein Dispute Delivery':   'creatordispute'},
              {'Rein Dispute Offer':      'workerdispute'},
              {'Rein Dispute Resolution': 'resolution'},
             ]
    for t in title:
        m = re.search('^'+t, text)
        if m:
            return titles[t]
    return None

def calc_hash(text):
    text = text.decode('ascii')
    text = text.encode('utf8')
    return hashlib.sha256(text).hexdigest()
