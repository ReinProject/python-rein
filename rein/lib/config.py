import os
from user import User

class Config():
    def __init__(self): 
        self.db_filename = 'local.db'
        self.backup_filename = 'backup-rein.json'
        self.enroll_filename = 'enrollment.txt'
        self.sig_enroll_filename = 'enrollment.txt.sig'
        self.config_dir = os.path.join(os.path.expanduser('~'), '.rein')
        self.multi = False

        if not os.path.isdir(self.config_dir):
            os.mkdir(self.config_dir)
    
    def has_no_account(self):
        if not os.path.isfile(os.path.join(self.config_dir, self.db_filename)) or \
            (self.multi or self.session.query(User).count() == 0):
            return True
        else:
            return False
