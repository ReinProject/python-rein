from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import click

Base = declarative_base()

class Wallet(Base):
    __tablename__ = 'wallet'

    address = Column(String(34), primary_key=True)
    privkey = Column(String(52))

    def __init__(self, session, address, privkey):
        self.address = address
        self.privkey = privkey
        session.add(self)
        session.commit()

    @classmethod
    def get(self, rein, address, default=False):
        res = rein.session.query(Wallet).filter(Wallet.address == address).first()
        if res:
            return res.privkey
        else:
            return default

    @classmethod
    def set(self, rein, address, privkey=''):
        res = rein.session.query(Wallet).filter(Wallet.address == address).first()
        if res:
            res.privkey = privkey
            rein.session.commit()
        else:
            p = Wallet(rein.session, address, privkey)
