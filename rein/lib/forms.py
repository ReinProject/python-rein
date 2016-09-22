from flask import Flask
from flask_wtf import Form
from wtforms import TextField, TextAreaField, RadioField, PasswordField
from wtforms.validators import Required, ValidationError
import config
from mediator import Mediator
from document import Document
from order import Order
from user import User
from bitcoinecdsa import privkey_to_address
from bitcoinaddress import check_bitcoin_address

from ui import build_enrollment
from validate import validate_enrollment


rein = config.Config()


def validate_privkey(form, field):
    if not privkey_to_address(field.data):
        raise ValidationError("Not a valid private key.")

def validate_address(form, field):
    if not check_bitcoin_address(field.data):
        raise ValidationError("Invalid address")

def validate_en(form, field):
    message = field.data
    print "r n s: " + str(message.find("\r\n"))
    print "n s: " + str(message.find("\n"))
    message = message.replace("\r\n","\n")
    print "r n s: " + str(message.find("\r\n"))
    print "n s: " + str(message.find("\n"))
    if not validate_enrollment(field.data):
        raise ValidationError("Invalid signature")

class SetupForm(Form):
    mediators = Mediator.get(None, rein.testnet)
    mediator_maddrs = []
    for m in mediators:
        mediator_maddrs.append((m.maddr, '{}</td><td>{}%</td><td>{}'.format(m.username,
                                                           m.mediator_fee,
                                                           m.dpubkey)))
    name = TextField('Name / Handle', validators = [Required()])
    contact = TextField('Email / Bitmessage', validators = [Required()])
    maddr = TextField('Master Bitcoin address', validators = [Required(), validate_address])
    daddr = TextField('Delegate Bitcoin address', validators = [Required(), validate_address])
    dkey = PasswordField('Delegate Bitcoin private Key', validators = [Required(), validate_privkey])
    will_mediate = RadioField('Register as a mediator?', choices = [('1','Yes'), ('0', 'No')])
    mediator_fee = TextField('Mediator Fee')  # TODO make required only if Yes above

class SignForm(Form):
    rein.user = User.get_newest(rein)
    if rein.user:
        enrollment = build_enrollment(rein)
    else:
        Exception("No enrollment to sign.")
    signed = TextAreaField('Signed enrollment', validators = [Required(), validate_en])

class JobPostForm(Form):
    mediators = Mediator.get(None, rein.testnet)
    mediator_maddrs = []
    for m in mediators:
        mediator_maddrs.append((m.maddr, '{}</td><td>{}%</td><td>{}'.format(m.username,
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
    bid_html = []
    for b in bids:
        o = Order.get_by_job_id(rein, b['Job ID'])
        if o.get_state(rein, Document) in ['bid', 'job_posting']:
        #bid_ids.append(b['id'])
            job_link = '<a href="/job/%s">%s</a>' % (b['Job ID'], b['Job name'])
            bid_ids.append((str(b['id']), '{}</td><td>{}</td><td>{}</td><td>{}'.format(job_link,
                                                               b['Worker'],
                                                               b['Description'],
                                                               b['Bid amount (BTC)'])))
    bid_id = RadioField('Choose bid', choices = bid_ids)

class AcceptForm(Form):
    deliveries = Document.get_by_type(rein, 'delivery')
    deliverables = []
    for d in deliveries:
        o = Order.get_by_job_id(rein, d['Job ID'])
        if o.get_state(rein, Document) in ['offer', 'delivery']:
            deliverables.append((str(d['id']), '{}</td><td>{}</td><td>{}'.format(d['Job name'],
                                                                d['Job ID'],
                                                                d['Deliverables'])))
    signed_primary_payment = TextAreaField('Signed primary payment', validators = [Required()])
    signed_mediator_payment = TextAreaField('Signed mediator payment', validators = [Required()])
    deliverable_id = RadioField('Choose deliverable to accept', choices = deliverables)
