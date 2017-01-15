from .market import assemble_document, sign_and_store_document
from .document import Document
from .io import safe_get
from sqlalchemy import and_

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