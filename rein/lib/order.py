from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
try:
    from document import Document
except:
    pass

Base = declarative_base()

FLOW = {
        'job_posting':    {'pre': [],                               'next': ['bid']},
        'bid':            {'pre': ['job_posting'],                  'next': ['offer']},
        'offer':          {'pre': ['bid'],                          'next': ['delivery', 'creatordispute', 'workerdispute']},
        'delivery':       {'pre': ['offer'],                        'next': ['accept', 'creatordispute', 'workerdispute']},
        'creatordispute': {'pre': ['offer', 'delivery'],            'next': ['resolve', 'workerdispute']},
        'workerdispute':  {'pre': ['offer', 'delivery', 'accept'],  'next': ['resolve', 'creatordispute']},
        'accept':         {'pre': ['delivery'],                     'next': ['workerdispute', 'complete']},
        'resolve':        {'pre': ['creatordispute', 'workerdispute'], 'next': ['complete']},
       }

PAST_TENSE = {
        'job_posting': 'posted',
        'bid': 'bid(s) submitted',
        'offer': 'job awarded',
        'delivery': 'deliverables submitted',
        'creatordispute': 'disputed by job creator',
        'workerdispute': 'disputed by worker',
        'accept': 'complete, work accepted',
        'resolve': 'complete, dispute resolved'
        }
# bid() hide job_posting if there is an offer
# deliver() hide offer if there is an accept
# offer() hide job_posting if there is an offer
# workerdispute() hide offer if there is an accept or resolution
# creatordispute() hide offer if there is a resolution
# resolution() hide *dispute if there is a resolution

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
            return rein.session.query(Document).filter(and_(Document.order_id == self.id,
                                                            Document.doc_type == doc_type)).all()
        else:
            return rein.session.query(Document).filter(Document.order_id == self.id).all()

    def get_state(self, rein, Document):
        documents = rein.session.query(Document).filter(Document.order_id == self.id).all()
        # find job_posting
        # walk from job_posting to find something from state[document.doc_type]['next']
        # when nothing from state[document.doc_type]['next'] can be found then
        # we may have found it, let's try that out.
        # for document in documents:
        #    if document.doc_type == 'job_posting':
        #        start = document
        current = 'job_posting'
        while 1:
            moved = False
            for document in documents:
                if document.doc_type in FLOW[current]['next']:
                    current = document.doc_type
                    moved = True
            if not moved:
                return current

    @classmethod
    def get_past_tense(self, state):
        return PAST_TENSE[state]

    @classmethod
    def get_user_orders(self, rein, Document):
        documents = rein.session.query(Document).filter(Document.identity == rein.user.id).all()
        order_ids = []
        for document in documents:
            if document.order_id not in order_ids:
                order_ids.append(document.order_id)
        orders = []
        for order_id in order_ids:
            order = rein.session.query(Order).filter(Order.id == order_id).first()
            if order:
                orders.append(order)
        return orders

    @classmethod
    def get_order_id(self, rein, job_id):
        order = rein.session.query(Order).filter(Order.job_id == job_id).first()
        if order:
            return order.id
        return None
