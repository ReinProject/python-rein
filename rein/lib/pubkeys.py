from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import click

Base = declarative_base()

class Pubkeys(Base):
    __tablename__ = 'pubkeys'

    pubkey = Column(String(34), primary_key=True)
    privkey = Column(String(52))

    def __init__(self, session, pubkey, privkey):
        self.pubkey = pubkey
        self.privkey = privkey
        session.add(self)
        session.commit()

    @classmethod
    def get(self, rein, pubkey, default=False):
        res = rein.session.query(Pubkeys).filter(Pubkeys.pubkey == pubkey).first()
        if res:
            return res.privkey
        else:
            return default

    @classmethod
    def set(self, rein, pubkey, privkey=''):
        res = rein.session.query(Pubkeys).filter(Pubkeys.pubkey == pubkey).first()
        if res:
            res.privkey = privkey
            rein.session.commit()
        else:
            p = Pubkeys(rein.session, pubkey, privkey)