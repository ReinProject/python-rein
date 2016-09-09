from flask import Flask
from flask_wtf import Form
from wtforms import TextField, TextAreaField, RadioField
from wtforms.validators import Required
import config
from mediator import Mediator
from document import Document

rein = config.Config()

class JobPostForm(Form):
    mediators = Mediator.get(None, rein.testnet)
    mediator_maddrs = []
    for m in mediators:
        mediator_maddrs.append((m.maddr, '{}</td><td>{}</td><td>{}'.format(m.username,
                                                           m.mediator_fee,
                                                           m.dpubkey)))
    print mediator_maddrs
    job_name = TextField('Job name', validators = [Required()])
    description = TextAreaField('Description', validators = [Required()])
    tags = TextField('Tags', validators = [Required()])
    expire_days = TextField('Expiration (days)', validators = [Required()])
    mediator_maddr = RadioField('Choose mediator', choices = mediator_maddrs)

class JobOfferForm(Form):
    bids = Document.get_by_type(rein, 'bid')
    bid_ids = []
    bid_html = []
    for b in bids:
        #bid_ids.append(b['id'])
        bid_ids.append((str(b['id']), '{}</td><td>{}</td><td>{}</td><td>{}'.format(b['Job name'],

                                                           b['Worker'],
                                                           b['Description'],
                                                           b['Bid amount (BTC)'])))
    print bid_ids
    bid_id = RadioField('Choose bid', choices = bid_ids)

class AcceptForm(Form):
    deliveries = Document.get_by_type(rein, 'delivery')
    deliverables = []
    for d in deliveries:
        deliverables.append(d['Deliverables'])
    signed_primary_payment = TextAreaField('Signed primary payment', validators = [Required()])
    signed_mediator_payment = TextAreaField('Signed mediator payment', validators = [Required()])
