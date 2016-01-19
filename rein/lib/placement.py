from sqlalchemy import Column, Integer, String, and_
from sqlalchemy.ext.declarative import declarative_base
import requests
import hashlib

Base = declarative_base()


class Placement(Base):
    __tablename__ = 'placement'

    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, nullable=False)
    url = Column(String(250), nullable=False)
    remote_key = Column(String(64), nullable=False)
    verified = Column(Integer, nullable=False)

    def __init__(self, doc_id, url, remote_key, verified=0):
        self.doc_id = doc_id
        self.url = url
        self.remote_key = remote_key
        self.verified = verified

    def set_verified(self):
        self.verified = 1

    def clear_verified(self):
        self.verified = 0

def get_placements(rein, url, doc_id):
    return rein.session.query(Placement).filter(and_(Placement.url == url,
                                                     Placement.doc_id == doc_id)).all()


def get_remote_document_hash(rein, plc):
    sel_url = "{0}get?key={1}"
    answer = requests.get(url=sel_url.format(plc.url, plc.remote_key))
    if answer.status_code == 404:
        rein.log.error("%s not found at %s" % (str(plc.doc_id), plc.url))
        return False
    else:
        text = answer.json()['value']
        text = text.decode('ascii')
        text = text.encode('utf8')
        return hashlib.sha256(text).hexdigest()
    

def create_placements(engine):
    Base.metadata.create_all(engine)
