from sqlalchemy import Column, Integer, String, Float, Boolean, and_
#from sqlalchemy import create_engine
#from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import requests
import click
import config
#import os
from validate import filter_and_parse_valid_sigs
from market import unique

Base = declarative_base()
rein = config.Config()

#engine = create_engine("sqlite:///%s" % os.path.join(rein.config_dir, rein.db_filename))
#Base.metadata.bind = engine
#DBSession = sessionmaker(bind=engine)
#session = DBSession()

class Mediator(Base):
    __tablename__ = 'mediator'

    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False)
    contact = Column(String(250), nullable=False)
    maddr = Column(String(64), nullable=False)
    daddr = Column(String(64), nullable=False)
    dpubkey = Column(String(64), nullable=False)
    will_mediate = Column(Boolean, nullable=False)
    mediator_fee = Column(Float, nullable=False)
    testnet = Column(Boolean, nullable=False)

    def __init__(self, m, testnet): #name, contact, maddr, daddr, dkey, will_mediate, mediator_fee, testnet):
        self.username = m[u'User']
        self.contact = m[u'Contact']
        self.maddr = m['Master signing address']
        self.daddr = m['Delegate signing address']
        self.dpubkey = m['Mediator public key']
        self.will_mediate = 1 if m['Willing to mediate'] else 0
        self.mediator_fee = m['Mediator fee'].replace("%",'')
        self.testnet = 1 if testnet else 0

    @classmethod
    def get(self, maddr, testnet):
        if maddr is None:
            res = rein.session.query(Mediator).all()
            ret = []
            for r in res:
                ret.append(r)
            return ret
        else:
            return rein.session.query(Mediator).filter(Mediator.maddr == maddr).all()

def get_mediators_bad(rein, user, urls, log):
    eligible_mediators = []
    blocks = []
    for url in urls:
        log.info("Querying %s for mediators..." % url)
        sel_url = "{0}query?owner={1}&query=mediators&testnet={2}"
        try:
            answer = requests.get(url=sel_url.format(url, user.maddr, rein.testnet))
        except:
            click.echo('Error connecting to server.')
            log.error('server connect error ' + url)
            continue
        data = answer.json()
        if len(data['mediators']) == 0:
            click.echo('None found')
        if data['block_info']:
            blocks.append(data['block_info'])
        eligible_mediators += filter_and_parse_valid_sigs(rein, data['mediators'])
    mediators = unique(eligible_mediators, 'Mediator public key')
    objs = []
    for m in mediators:
        newMediator = Mediator(m[u'User'], m[u'Master signing address'], m[u'Mediator public key'], m[u'Mediator fee'])
        objs.append(newMediator)
    return objs
