from .market import assemble_document, sign_and_store_document
from .document import Document
from .io import safe_get
from .order import Order, STATE
from .document import Document
from .bitcoinaddress import generate_sin
from sqlalchemy import and_
import json

def get_job_info(rein, order):
    """Returns necessary info about a given job"""
    job_id = ''
    job_name = ''
    employer_SIN = ''
    employer_name = ''
    mediator_SIN = ''
    mediator_name = ''
    employee_SIN = ''
    employee_name = ''

    bid = order.get_documents(rein, Document, 'bid')[0]
    bid_dict = bid.to_dict()
    posting = order.get_documents(rein, Document, 'job_posting')[0]
    posting_dict = posting.to_dict()

    job_id = bid_dict['Job ID']
    job_name = bid_dict['Job name']
    employee_SIN = generate_sin(bid_dict['Worker master address'])
    employee_name = bid_dict['Worker']
    employer_SIN = generate_sin(posting_dict['Job creator master address'])
    employer_name = posting_dict['Job creator']
    mediator_SIN = generate_sin(posting_dict['Mediator master address'])
    mediator_name = posting_dict['Mediator']

    return (job_id, job_name, employer_SIN, employer_name, mediator_SIN, mediator_name, employee_SIN, employee_name)

def get_user_jobs(rein):
    """Returns a list of orders (jobs) relevant for rating"""
    relevant_orders = []

    # Get user's jobs
    Order.update_orders(rein, Document)
    orders = Order.get_user_orders(rein, Document)
    for o in orders:
        setattr(o,'state',STATE[o.get_state(rein, Document)]['past_tense'])
        # Enable rating only for jobs that are completed
        if o.state == 'complete, work accepted' or o.state == 'dispute resolved':
            relevant_orders.append(o)

    job_list = []
    for order in relevant_orders:
        (job_id, job_name, employer_SIN, employer_name, mediator_SIN, mediator_name, employee_SIN, employee_name) = get_job_info(rein, order)
        
        job = {
            'job_id': job_id, 
            'job_name': job_name,
            'employer': {'SIN': employer_SIN, 'Name': employer_name}, 
            'mediator': {'SIN': mediator_SIN, 'Name': mediator_name}, 
            'employee': {'SIN': employee_SIN, 'Name': employee_name}
        }
        job_list.append(job)

    return json.dumps(job_list)

def rating_identifier(fields):
	"""Generates a string that would be found in the contents of an existing rating document"""
	identifier = ''
	relevant_fields = ['User id', 'Job id', 'Rater id']
	for field in fields:
		if field['label'] in relevant_fields:
			identifier += field['label'] + ": " + field['value'] + "\n"

	return identifier

def add_rating(rein, user, testnet, rating, user_msin, job_id, rated_by_msin, comments):
    """Adds a rating to the database or updates it if an already existing
    rating is adjusted"""
    fields = [
        {'label': 'Rating',     'value': rating},
        {'label': 'User msin',    'value': user_msin},
        {'label': 'Job id',     'value': job_id},
        {'label': 'Rater msin',   'value': rated_by_msin},
        {'label': 'Comments',   'value': comments},
     ]
    
    document_text = assemble_document('Rating', fields)
    update_identifier = rating_identifier(fields)
    look_for = '%\n{}%'.format(update_identifier)
    update_rating = rein.session.query(Document).filter(and_(Document.testnet == testnet, Document.contents.like(look_for))).first()

    store = True
    document = None
    if update_rating:
    	document = sign_and_store_document(rein, 'rating', document_text, user.daddr, user.dkey, store, update_rating.doc_hash)

    else:
    	document = sign_and_store_document(rein, 'rating', document_text, user.daddr, user.dkey, store)
    
    return (document and store)