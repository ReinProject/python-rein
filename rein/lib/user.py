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
    dxprv = Column(String(250), nullable=False)
    will_mediate = Column(Boolean, nullable=False)
    mediator_fee = Column(Float, nullable=False)
    enrolled = Column(Boolean, nullable=False)
    testnet = Column(Boolean, nullable=False)

    def __init__(self, name, contact, maddr, daddr, dkey, dxprv, will_mediate, mediator_fee, testnet):
        self.name = name
        self.contact = contact
        self.maddr = maddr
        self.daddr = daddr
        self.dkey = dkey
        self.dxprv = dxprv
        self.enrolled = False
        self.testnet = testnet

        if will_mediate == u'1':
            self.will_mediate = True
        else:
            self.will_mediate = False

        if self.will_mediate:
            self.mediator_fee = float(mediator_fee)
        else:
            self.mediator_fee = 0

    @classmethod
    def get_newest(self, rein):
        return rein.session.query(User).filter(User.enrolled == 0).order_by(User.id.desc()).first()

    @classmethod
    def get(self, rein, id):
        return rein.session.query(User).get(id)

    @classmethod
    def set_enrolled(self, rein, user):
        user.enrolled = True
        rein.session.commit()
