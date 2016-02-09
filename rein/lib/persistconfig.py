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
        return self

    def set(self, rein, key, value=''):
        self.key = value
        rein.session.commit()

    @classmethod
    def set_testnet(self, rein, value):
        res = rein.session.query(PersistConfig).filter(PersistConfig.key == 'testnet').first()
        if res:
            res.value = value
        else:
            p = PersistConfig(rein.session, 'testnet', value)
            click.echo(p)
            rein.session.add(p)
        rein.session.commit()

    @classmethod
    def get_testnet(self, rein):
        res = rein.session.query(PersistConfig).filter(PersistConfig.key == 'testnet').first()
        if res and res.value == 'true':
            return True
        else:
            return False
