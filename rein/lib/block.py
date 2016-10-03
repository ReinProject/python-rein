from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

"""
  "hash": "000000000000000007365300be19da64650e30d244e590c536c42129aeca574b",
  "height": 368129,
  "time": 1438545083,
"""


class Block(Base):
    __tablename__ = 'block'

    hash = Column(String(64), primary_key=True)
    time = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)

    def __init__(self, hash, time, height):
        self.hash = hash
        self.time = time
        self.height = height

    @classmethod
    def get_time(self, rein, hash):
        block = rein.session.query(self).get(hash)
        if block:
            return block.time
        else:
            return None
