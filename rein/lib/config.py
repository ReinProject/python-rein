import os
import logging
import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from user import User, Base
from persistconfig import PersistConfig


class Config():
    def __init__(self):
        self.db_filename = 'local.db'
        self.backup_filename = 'backup-rein.json'
        self.enroll_filename = 'enrollment.txt'
        self.sig_enroll_filename = 'enrollment.txt'
        self.config_dir = os.path.join(os.path.expanduser('~'), '.rein')
        self.user = None
        self.multi = False

        self.setup_logging()
        self.log.info('starting python-rein')
        self.setup_db()
        self.log.info('database connected')
        self.testnet = 1 if PersistConfig.get_testnet(self) else 0
        self.tor = 1 if PersistConfig.get_tor(self) else 0
        if self.tor:
            self.proxies = { 'http': 'socks5://127.0.0.1:9150' }
        else:
            self.proxies = {}
        self.log.info('testnet = ' + str(self.testnet))

    def setup_logging(self):
        self.log = logging.getLogger('python-rein')
        self.log.setLevel(logging.INFO)
        handler = logging.FileHandler(os.path.join(os.path.expanduser('~'), '.rein', "rein.log"))
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

    def setup_db(self):
        self.engine = create_engine("sqlite:///%s" % os.path.join(self.config_dir, self.db_filename), connect_args = {'check_same_thread':False})
        Base.metadata.bind = self.engine
        DBSession = sessionmaker(bind=self.engine)
        self.session = DBSession()
        Base.metadata.create_all(self.engine)

    def setup_tor(self):
        import socket
        import socks
        socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 9150)
        socket.socket = socks.socksocket

    def set_multiuser(self):
        self.multi = True

    def get_log(self):
        return self.log

    def has_no_account(self):
        if not os.path.isfile(os.path.join(self.config_dir, self.db_filename)) or \
           self.session.query(User).filter(User.testnet == self.testnet).count() == 0:
            return True
        else:
            return False
