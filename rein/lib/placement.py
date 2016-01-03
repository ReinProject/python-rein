from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Placement(Base):
    __tablename__ = 'placement'

    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, nullable=False)
    url = Column(String(250), nullable=False)
    remote_key = Column(String(64), nullable=False)
    verified = Column(Integer, nullable=False)

    def __init__(self, doc_id, url):
        self.doc_id = doc_id
        self.url = url

    def set_verified():
        self.verified = 1

    def clear_verified():
        self.verified = 0

def create_placements(engine):
    Base.metadata.create_all(engine)
