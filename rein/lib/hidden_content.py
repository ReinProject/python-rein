import random

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class HiddenContent(Base):
    """Model to hold settings regarding what content is hidden."""

    __tablename__ = 'hidden_content'

    id = Column(Integer, primary_key=True)
    content_type = Column(String(32))
    content_identifier = Column(String(128))
    content_description = Column(String)

    def __init__(self, content_type, content_identifier, content_description=''):
        """Sets the content that is supposed to be hidden."""

        self.content_type = content_type
        self.content_identifier = content_identifier
        self.content_description = content_description

    @staticmethod
    def get_hidden_content(rein, content_type):
        """Gets all content identifiers of content type that are hidden."""

        hidden_content_db = rein.session.query(HiddenContent).filter(HiddenContent.content_type == content_type).all()
        hidden_content = []
        for content in hidden_content_db:
            hidden_content.append({'content_identifier': content.content_identifier, 'content_description': content.content_description})

        return hidden_content

    @staticmethod
    def hide_button(content_type, content_identifier, content_description=''):
        """Generates a button to hide list content.
        Type can be 'job', 'bid' or 'mediator' with content_identifier being
        that item's unique id (job id, bid doc hash, or msin)."""

        button_id = random.getrandbits(32)
        # Sanitize input
        content_description = content_description.replace('"', '&quot;').replace("'", "&quot;")
        return '<button type="button" onclick="hide(\'{}\', \'{}\', \'{}\', \'{}\')" id="{}">Hide&nbsp;{}</button>'.format(content_type, content_identifier, content_description, button_id, button_id, content_type)

    @staticmethod
    def unhide_button(content_type, content_identifier):
        """Generates a button to hide list content.
        Type can be 'job', 'bid' or 'mediator' with content_identifier being
        that item's unique id (job id, bid doc hash, or msin)."""

        button_id = random.getrandbits(32)
        return '<button type="button" onclick="unhide(\'{}\', \'{}\', \'{}\')" id="{}">Unhide {}</button>'.format(content_type, content_identifier, button_id, button_id, content_type)
