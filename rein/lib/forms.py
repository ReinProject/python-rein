from flask import Flask
from flask_wtf import Form
from wtforms import TextField, TextAreaField, RadioField, PasswordField, HiddenField
from wtforms.validators import Required, ValidationError
import rein.lib.config as config
from .mediator import Mediator
from .document import Document
from .order import Order
from .bitcoinecdsa import privkey_to_address
from .bitcoinaddress import check_bitcoin_address

from .ui import build_enrollment
from .validate import validate_enrollment


def validate_privkey(form, field):
    if not privkey_to_address(field.data):
        raise ValidationError("Not a valid private key.")

def validate_address(form, field):
    if not check_bitcoin_address(field.data):
        raise ValidationError("Invalid address")

def validate_en(form, field):
    message = field.data.replace("\r\n","\n")
    if not validate_enrollment(message):
        raise ValidationError("Invalid signature")

def validate_mediator_fee(form, field):
    try:
        float(field.data)
    except ValueError:
        raise ValidationError("Invalid mediator fee")

class SetupForm(Form):
    name = TextField('Name / Handle', validators = [Required()])
    contact = TextField('Email / Bitmessage', validators = [Required()])
    maddr = TextField('Master Bitcoin address', validators = [Required(), validate_address])
    daddr = TextField('Delegate Bitcoin address', validators = [Required(), validate_address])
    dkey = PasswordField('Delegate Bitcoin private Key', validators = [Required(), validate_privkey])
    will_mediate = RadioField('Register as a mediator?', choices = [('1','Yes'), ('0', 'No')])
    mediator_fee = TextField('Mediator Fee', validators = [validate_mediator_fee])  # TODO make required only if Yes above

class SignForm(Form):
    identity_id = HiddenField("identity_id")
    signed = TextAreaField('Signed enrollment', validators = [Required(), validate_en])

class JobPostForm(Form):
    job_name = TextField('Job name', validators = [Required()])
    description = TextAreaField('Description', validators = [Required()])
    tags = TextField('Tags', validators = [Required()])
    expire_days = TextField('Expiration (days)', validators = [Required()])
    mediator_maddr = RadioField('Choose mediator')

class BidForm(Form):
    description = TextAreaField('Description', validators = [Required()])
    bid_amount = TextAreaField('Bid amount', validators = [Required()])
    job_id = RadioField('Choose Job to bid on')

class JobOfferForm(Form):
    bid_id = RadioField('Choose bid')

class DeliverForm(Form):
    deliverable = TextAreaField('Deliverables', validators = [Required()])
    job_id = RadioField('Choose job associated with deliverables')

class DisputeForm(Form):
    dispute_detail = TextAreaField('Dispute detail', validators = [Required()])
    order_id = RadioField('Choose job')

class AcceptForm(Form):
    deliverable_id = RadioField('Deliverables')

class ResolveForm(Form):
    resolution = TextAreaField('Resolution', validators = [Required()])
    client_payment_amount = TextField('Client payment amount', validators = [Required()])
    dispute_id = RadioField('Disputes')

class AcceptResolutionForm(Form):
    resolution_id = RadioField('Resolution')
