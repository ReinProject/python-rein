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

