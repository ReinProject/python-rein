from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from .user import User

Base = declarative_base()


class Rating(Base):
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)
    user_id = Column(String(64), ForeignKey(User.msin))
    user = relationship(User, backref="ratings", foreign_keys=[user_id])
    job_id = Column(String(64), nullable=False)
    rated_by_id = Column(String(64), ForeignKey(User.msin))
    rated_by = relationship(User, backref="has_rated", foreign_keys=[rated_by_id])
    comments = Column(Text, nullable=True)

    def __init__(self, rating, user_id, job_id, rated_by_id, comments):
        self.rating = rating
        self.user_id = user_id
        self.job_id = job_id
        self.rated_by_id = rated_by_id
        self.comments = comments