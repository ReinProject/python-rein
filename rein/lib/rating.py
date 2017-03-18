from flask import flash

from .market import assemble_document, sign_and_store_document
from .document import Document
from .io import safe_get
from .util import document_to_dict, get_user_name
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

def get_user_jobs(rein, return_dict=False):
    """Returns a list of ten most recent orders (jobs) relevant for rating"""
    relevant_orders = []

    # Get user's jobs
    Order.update_orders(rein, Document)
    orders = Order.get_user_orders(rein, Document)
    for o in orders:
        setattr(o,'state',STATE[o.get_state(rein, Document)]['past_tense'])
        # Enable rating only for jobs that are completed
        relevant_states = ['complete, work accepted', 'dispute resolved'] # For testing 'job awarded'
        if o.state in relevant_states:
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

    if job_list:
        # Limit list to ten most recent jobs in reverse chronological order
        job_list.reverse()
        job_list = job_list[0:10]

    if return_dict:
        return job_list

    return json.dumps(job_list)

def rating_identifier(fields):
	"""Generates a string that would be found in the contents of an existing rating document"""
	identifier = ''
	relevant_fields = ['User msin', 'Job id', 'Rater msin']
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
    update_rating = rein.session.query(Document).filter(and_(Document.testnet == testnet, Document.contents.like(look_for), Document.doc_type == 'rating')).first()

    store = True
    document = None
    if update_rating:
    	flash(u"Ratings cannot currently be updated.")

    else:
    	document = sign_and_store_document(rein, 'rating', document_text, user.daddr, user.dkey, store)
    
    return (document and store)


def get_average_user_rating(log, url, user, rein, msin):
    """Gets the average rating a user (identified by his msin) has received
    along with the number of ratings he has received"""

    ratings = rein.session.query(Document).filter(and_(
        Document.testnet == rein.testnet,
        Document.contents.like('%\nRein Rating%')
    )).filter(
        Document.contents.like('%\nUser msin: {}%'.format(msin))
    ).limit(100).all()

    # Create a list of all the ratings the user has received
    rating_values = []
    for rating_data in ratings:
        rating = document_to_dict(rating_data.contents)
        try:
            rating_value = int(rating['Rating'])
            rating_values.append(rating_value)

        except:
            pass

    # Return None if the user has not been rated
    if len(rating_values) == 0:
        return None

    average_rating = float(sum(rating_values)) / float(len(rating_values))
    return (average_rating, len(rating_values))

def get_average_user_rating_display(log, url, user, rein, msin, cli=False):
    """Returns a user's average rating in html format (as a link to the user's ratings page)."""

    rating = get_average_user_rating(log, url, user, rein, msin)
    if not rating:
        return 'Not yet rated'

    if not cli:
        return '{} <i class="fa fa-star"></i> <small>(<a href="/ratings/{}">{}</a>)</small>'.format(rating[0], msin, rating[1])

    return '{} Stars ({})'.format(rating[0], rating[1]) 

def get_all_user_ratings(log, url, user, rein, msin):
    """Returns a list of a user's ratings."""

    rating_docs = rein.session.query(Document).filter(and_(
        Document.testnet == rein.testnet,
        Document.contents.like('%\nRein Rating%')
    )).filter(
        Document.contents.like('%\nUser msin: {}%'.format(msin))
    ).limit(100).all()

    # Create a list of all the ratings the user has received
    ratings = []
    for rating_data in rating_docs:
        rating = document_to_dict(rating_data.contents)
        ratings.append(
            {
                'rating_value': '{} <i class="fa fa-star"></i>'.format(float(rating['Rating'])),
                'comments': rating['Comments'],
                'rated_by_name': get_user_name(log, url, user, rein, rating['Rater msin']),
                'rated_by_rating': get_average_user_rating_display(log, url, user, rein, rating['Rater msin'])
            }
        )

    return ratings

def calculate_trust_score(dest_msin=None, source_msin=None, rein=None, test=False, test_ratings=[]):
    """Calculates the trust score for a user as identified by his msin.
    Algorithm based on the level 2 trust system implemented by Bitcoin OTC
    and outlined at https://wiki.bitcoin-otc.com/wiki/OTC_Rating_System#Notes_about_gettrust."""

    # Grab all ratings commited by source_msin (the client)
    ratings_by_source = None
    if not test:
        ratings_by_source = rein.session.query(Document).filter(and_(
            Document.doc_type == 'rating',
            Document.contents.like('%\nRater msin: {}%'.format(source_msin))
        )).all()

    else:
        ratings_by_source = [test_rating for test_rating in test_ratings if test_rating['Rater msin'] == 'SourceMsin']

    # Compile list of users (by msin) that have been rated by source and their ratings
    rated_by_source = []
    for rating in ratings_by_source:
        rating_dict = None
        if not test:
            rating_dict = document_to_dict(rating.contents)

        else:
            rating_dict = rating

        msin_rated = rating_dict['User msin']
        rating_value = int(rating_dict['Rating'])
        if not msin_rated in rated_by_source:
            rated_by_source.append((msin_rated, rating_value))

    # Determine if any of the users rated by source or source have rated dest
    # Add source to the list of users source has vouched for with full trust
    vouched_users = rated_by_source + [(source_msin, 5)]
    # Calculate trust links between source and dest
    trust_links = []
    for vouched_user in vouched_users:
        (vouched_user_msin, vouched_user_trust) = vouched_user
        dest_ratings_by_vouched_user = None
        if not test:
            dest_ratings_by_vouched_user = rein.session.query(Document).filter(
                and_(
                    Document.doc_type == 'rating',
                    Document.contents.like('%\nRater msin: {}%'.format(vouched_user_msin)),
                    Document.contents.like('%\nUser msin: {}%'.format(dest_msin))
                )).all()
        else:
            dest_ratings_by_vouched_user = [test_rating for test_rating in test_ratings if test_rating['Rater msin'] == vouched_user_msin and test_rating['User msin'] == 'DestMsin']

        for rating in dest_ratings_by_vouched_user:
            link_rating = None
            if not test:
                link_rating = document_to_dict(rating.contents)

            else:
                link_rating = rating

            trust_values = [
                vouched_user_trust, 
                int(link_rating['Rating'])
            ]
            trust_links.append(min(trust_values))

    dest_trust_score = {
            'score': 0, 
            'links': 0
    }
    if len(trust_links) != 0:
        dest_trust_score['score'] = float(sum(trust_links)) / float(len(trust_links))
        dest_trust_score['links'] = len(trust_links)        
    if not test:
        dest_trust_score = json.dumps(dest_trust_score)
        
    return dest_trust_score
