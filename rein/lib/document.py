import hashlib
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

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

def get_user_documents(rein):
    return rein.session.query(Document).filter(Document.identity == rein.user.id).all()
