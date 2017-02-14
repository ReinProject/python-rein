from sqlalchemy import Column, Integer, String, Float, Boolean, and_
from sqlalchemy.ext.declarative import declarative_base

import click
import rein.lib.config as config

from .validate import filter_and_parse_valid_sigs
from .util import unique

Base = declarative_base()
rein = config.Config()

class Mediator(Base):
    __tablename__ = 'mediator'

    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False)
    contact = Column(String(250), nullable=False)
    maddr = Column(String(64), nullable=False)
    msin = Column(String(64), nullable=False)
    daddr = Column(String(64), nullable=False)
    dpubkey = Column(String(64), nullable=False)
    will_mediate = Column(Boolean, nullable=False)
    mediator_fee = Column(Float, nullable=False)
    testnet = Column(Boolean, nullable=False)

    def __init__(self, m, testnet): #name, contact, maddr, daddr, dkey, will_mediate, mediator_fee, testnet):
        self.username = m[u'User']
        self.contact = m[u'Contact']
        self.maddr = m['Master signing address']
        self.msin = m['Secure Identity Number']
        self.daddr = m['Delegate signing address']
        self.dpubkey = m['Mediator public key']
        self.will_mediate = 1 if m['Willing to mediate'] else 0
        self.mediator_fee = m['Mediator fee'].replace("%",'')
        self.testnet = 1 if testnet else 0

    @classmethod
    def get(self, maddr, testnet):
        if maddr is None:
            res = rein.session.query(Mediator).filter(Mediator.testnet == testnet).all()
            ret = []
            for r in res:
                ret.append(r)
            return ret
        else:
            return rein.session.query(Mediator).filter(Mediator.maddr == maddr,
                                                       Mediator.testnet == testnet).all()
