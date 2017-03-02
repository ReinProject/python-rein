from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class HiddenContent(Base):
    """Model to hold settings regarding what content is hidden."""

    __tablename__ = 'hidden_content'

    id = Column(Integer, primary_key=True)
    content_type = Column(String(32))
    content_identifier = Column(String(128))

    def __init__(self, content_type, content_identifier):
        """Sets the content that is supposed to be hidden."""

        self.content_type = content_type
        self.content_identifier = content_identifier

    @staticmethod
    def get_hidden_ids(rein, content_type):
        """Gets all content identifiers of content type that are hidden."""

        hidden_content = rein.session.query(HiddenContent).filter(HiddenContent.content_type == content_type).all()
        hidden_ids = []
        for content in hidden_content:
            hidden_ids.append(content.content_identifier)

        return hidden_ids