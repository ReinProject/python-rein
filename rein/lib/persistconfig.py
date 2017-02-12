from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import click

Base = declarative_base()


class PersistConfig(Base):
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True)
    key = Column(String(255))
    value = Column(String(255))

    def __init__(self, session, key, value):
        self.key = key
        self.value = value
        session.add(self)
        session.commit()

    @classmethod
    def get(self, rein, key, default=False):
        res = rein.session.query(PersistConfig).filter(PersistConfig.key == key).first()
        if res and res.value == 'true':
            return True
        elif res and res.value == 'false':
            return False
        elif res:
            return res.value
        else:
            return default

    @classmethod
    def set(self, rein, key, value=''):
        res = rein.session.query(PersistConfig).filter(PersistConfig.key == key).first()
        if res:
            res.value = value
        else:
            p = PersistConfig(rein.session, key, value)
            rein.session.add(p)
        rein.session.commit()
