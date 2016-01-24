from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
try:
    from document import Document
except:
    pass

Base = declarative_base()


class Order(Base):
    __tablename__ = 'order'

    id = Column(Integer, primary_key=True)
    job_id = Column(String(32), nullable=False)
    posting_doc_id = Column(Integer, nullable=True)
    job_creator_maddr = Column(String(64), nullable=True)
    mediator_maddr = Column(String(64), nullable=True)
    worker_maddr = Column(String(64), nullable=True)
    job_creator = Column(Integer, nullable=True)
    open_for_bid = Column(Boolean, nullable=True)

    def __init__(self, job_id):
        self.job_id = job_id

    # what should an order be able to do? it should be able to hand you 
    # ids for valid documents for each step in the process. so there
    # should only be one posting. the job id should be the sha hash of the
    # signed document which should be impossible to collide. add a nonce i guess
    # and make the hash of the document be a certain size.

    # we do this download of a bunch of new docs from the server
    def attach_documents(self, job_id):
        documents = self.get_documents()
        for doc in documents:
            doc.set_order_id(self.id)

    def get_documents(self, doc_type=None):
        if doc_type:
            return rein.session.query(Document).filter(and_(Document.order_id == order_id,
                                                            Document.doc_type == doc_type)).all()
        else:
            return rein.session.query(Document).filter(Document.order_id == order_id).all()

    @classmethod
    def get_order_id(self, rein, job_id):
        order = rein.session.query(Order).filter(Order.job_id == job_id).first()
        if order:
            return order.id
        return None
