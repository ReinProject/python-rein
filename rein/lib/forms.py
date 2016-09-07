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
    job_name = TextField('Job name', validators = [Required()])
    description = TextAreaField('Description', validators = [Required()])
    tags = TextField('Tags', validators = [Required()])
    expire_days = TextField('Expiration (days)', validators = [Required()])
    mediator_maddr = RadioField('Choose mediator', choices = mediator_maddrs)

class JobOfferForm(Form):
    bids = Document.get_by_type(rein, 'bid')
    bid_ids = []
    for b in bids:
        bid_ids.append((b['id'], '{}</td><td>{}</td><td>{}'.format(b['Job name'],
                                                           b['Worker'],
                                                           b['Description'],
                                                           b['Bid amount (BTC)'])))
    bid_id = RadioField('Choose Bid', choices = bid_ids)
