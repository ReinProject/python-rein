from flask import Flask
from flask_wtf import Form
from wtforms import TextField, TextAreaField, RadioField, PasswordField, HiddenField
from wtforms.validators import Required, ValidationError
import config
from mediator import Mediator
from document import Document
from order import Order
from bitcoinecdsa import privkey_to_address
from bitcoinaddress import check_bitcoin_address

from ui import build_enrollment
from validate import validate_enrollment


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
    signed_primary_payment = TextAreaField('Signed primary payment', validators = [Required()])
    signed_mediator_payment = TextAreaField('Signed mediator payment', validators = [Required()])
    deliverable_id = RadioField('Deliverables')

class ResolveForm(Form):
    signed_primary_payment = TextAreaField('Signed primary payment', validators = [Required()])
    signed_mediator_payment = TextAreaField('Signed mediator payment', validators = [Required()])
    resolution = TextAreaField('Resolution', validators = [Required()])
    dispute_id = RadioField('Disputes')
