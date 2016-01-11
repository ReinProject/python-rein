import click
from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'identity'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    contact = Column(String(250), nullable=False)
    maddr = Column(String(64), nullable=False)
    daddr = Column(String(64), nullable=False)
    dkey = Column(String(64), nullable=False)
    will_mediate = Column(Boolean, nullable=False)
    mediation_fee = Column(Float, nullable=False)

    def __init__(self, name, contact, maddr, daddr, dkey, will_mediate, mediation_fee):
        self.name = name
        self.contact = contact
        self.maddr = maddr
        self.daddr = daddr
        self.dkey = dkey
        self.will_mediate = will_mediate
        self.mediation_fee = mediation_fee
