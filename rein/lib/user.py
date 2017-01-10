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
    # Temporary nullable to keep backwards compatibility with v0.2.0 backup files
    dxprv = Column(String(250), nullable=True)
    msin = Column(String(64), nullable=True)
    will_mediate = Column(Boolean, nullable=False)
    mediator_fee = Column(Float, nullable=False)
    enrolled = Column(Boolean, nullable=False)
    testnet = Column(Boolean, nullable=False)

    def __init__(self, user_data):
        self.name = user_data['name']
        self.contact = user_data['contact']
        self.maddr = user_data['maddr']
        self.daddr = user_data['daddr']
        self.dkey = user_data['dkey']
        self.dxprv = user_data['dxprv']
        self.msin = user_data['msin']
        self.enrolled = False
        self.testnet = user_data['testnet']

        if user_data['will_mediate'] == u'1':
            self.will_mediate = True
        else:
            self.will_mediate = False

        if self.will_mediate:
            self.mediator_fee = float(user_data['mediator_fee'])
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
