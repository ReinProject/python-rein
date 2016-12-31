import hashlib
import re
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, and_
from sqlalchemy.ext.declarative import declarative_base
from .validate import filter_valid_sigs, parse_document
from .order import Order
from .io import safe_get

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
    testnet = Column(Boolean, nullable=False)

    titles = {'Rein User Enrollment':    'enrollment',
              'Rein Job':                'job_posting',
              'Rein Bid':                'bid',
              'Rein Offer':              'offer',
              'Rein Delivery':           'delivery',
              'Rein Accept Delivery':    'accept',
              'Rein Accept':             'accept',
              'Rein Dispute Delivery':   'creatordispute',
              'Rein Dispute Offer':      'workerdispute',
              'Rein Dispute Resolution': 'resolution',
             }

    def __init__(self, rein, doc_type, contents, order_id = None,
            source_url='local', source_key=None, sig_verified=False, testnet=True):
        self.identity = rein.user.id
        self.doc_type = doc_type  # enrollment, bid, offer, job, for_hire,
        self.doc_hash = hashlib.sha256(contents).hexdigest()
        self.contents = contents
        self.source_url = source_url
        self.source_key = source_key
        self.sig_verified = sig_verified
        self.order_id = order_id
        self.testnet = testnet

    def get_hash(self):
        return self.doc_hash

    def set_order_id(self, id):
        self.order_id = id

    @staticmethod
    def get(rein, id):
        return rein.session.query(Document).get(id)

    @staticmethod
    def get_user_documents(rein):
        return rein.session.query(Document).filter(and_(Document.identity == rein.user.id,
                                                        Document.source_url == 'local',
                                                        Document.testnet == rein.testnet)).all()

    @staticmethod
    def find(rein, doc_hash, source_url):
        res = rein.session.query(Document).filter(and_(Document.doc_hash == doc_hash,
                                                       Document.source_url == source_url)).all()
        return res

    @staticmethod
    def get_by_type(rein, doc_type):
        docs = rein.session.query(Document).filter(and_(Document.testnet == rein.testnet,
                                                        Document.source_url == 'remote')).all()

        # convert doc_type to nice title (bid -> "Rein Bid")
        target = ''
        for title in Document.titles:
            if Document.titles[title] == doc_type:
                target = title
        if not target:
            Exception('Non-existent doc_type requested')

        res = []
        for d in docs:
            parsed = parse_document(d.contents)
            if 'Title' in parsed:
                if parsed['Title'] == target:
                    parsed['id'] = d.id
                    res.append(parsed)
        return res

    @staticmethod
    def get_documents_by_job_id(rein, url, job_id):
        sel_url = "{0}query?owner={1}&query=by_job_id&job_ids={2}&testnet={3}"

        data = safe_get(rein.log, sel_url.format(url, rein.user.maddr, job_id, rein.testnet))

        if data and 'by_job_id' in data:
            return filter_valid_sigs(rein, data['by_job_id'])
        else:
            return None

    @staticmethod
    def get_job_id(text):
        m = re.search('Job ID: (.+)\n', text)
        if m:
            return m.group(1)
        else:
            return None

    @staticmethod
    def get_document_type(document):
        parsed = parse_document(document)
        if 'Title' in parsed:
            return Document.titles[parsed['Title']]
        return None

    @staticmethod
    def calc_hash(text):
        text = text.decode('ascii')
        text = text.encode('utf8')
        return hashlib.sha256(text).hexdigest()
