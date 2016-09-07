import hashlib
import requests
import re
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, and_
from sqlalchemy.ext.declarative import declarative_base
from validate import filter_valid_sigs, parse_document
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
    testnet = Column(Boolean, nullable=False)

    titles = {'Rein User Enrollment':    'enrollment',
              'Rein Job':                'job_posting',
              'Rein Bid':                'bid',
              'Rein Offer':              'offer',
              'Rein Delivery':           'delivery',
              'Rein Accept Delivery':    'accept',
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
    def get(id):
        return rein.session.query(Document).get(id)

    @staticmethod
    def get_user_documents(rein):
        return rein.session.query(Document).filter(and_(Document.identity == rein.user.id,
                                                        Document.source_url == 'local',
                                                        Document.testnet == rein.testnet)).all()

    @staticmethod
    def get_by_type(rein, doc_type):
        docs = rein.session.query(Document).filter(Document.testnet == rein.testnet).all()

        # convert doc_type to nice title (bid -> "Rein Bid")
        target = ''
        for title in Document.titles:
            if Document.titles[title] == doc_type:
                target = title
        if not target:
            raise('Non-existent doc_type requested')

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
        try:
            answer = requests.get(url=sel_url.format(url, rein.user.maddr, job_id, rein.testnet))
        except requests.exceptions.ConnectionError:
            rein.log.warning('Could not reach %s.' % url)
            return None
        data = answer.json()
        if len(data['by_job_id']) == 0:
            rein.log.warning('None found.')
        return filter_valid_sigs(rein, data['by_job_id'])

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
