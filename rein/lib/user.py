import click
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'identity'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    contact = Column(String(250), nullable=False)

    def __init__(self, name, contact):
        self.name = name
        self.contact = contact


def create_account(engine, session, name, contact):
    Base.metadata.create_all(engine)
    name = click.prompt("Enter name or handle", type=str)
    contact = click.prompt("Enter email or BitMessage address", type=str)
    new_identity = User(name, cnentact)
    session.add(new_identity)
    session.commit()

    data = {'name': name, 'contact': contact}
    backup_filename = 'rein-backup.json'
    if not os.path.isfile(backup_filename):
        f = open(backup_filename,'w')
        try:
            f.write(json.dumps(data))
            click.echo("Backup saved successfully to %s" % backup_filename)
        except:
            raise RuntimeError('Problem writing user details to json backup file.')
        f.close()
    else:
        click.echo("Backup flie already exists. Please run with --backup to save "\
                   "user details to file.")

def import_account(engine, session):
    Base.metadata.create_all(engine)
    backup_filename = click.prompt("Enter backup file name", type=str, default='rein-backup.json')    
    f = open(backup_filename, 'r')
    try:
        data = json.loads(f.read())
    except:
        raise RuntimeError('Backup file %s not valid json.' % backup_filename)
    new_identity = User(data['name'], data['contact'])
    session.add(new_identity)
    session.commit()
