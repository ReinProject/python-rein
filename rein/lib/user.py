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
    mediator_fee = Column(Float, nullable=False)
    enrolled = Column(Boolean, nullable=False)

    def __init__(self, name, contact, maddr, daddr, dkey, will_mediate, mediator_fee):
        self.name = name
        self.contact = contact
        self.maddr = maddr
        self.daddr = daddr
        self.dkey = dkey
        self.will_mediate = will_mediate
        self.mediator_fee = mediator_fee
        self.enrolled = False

    @classmethod
    def set_enrolled(self, rein, user):
        user.enrolled = True
        rein.session.commit()
