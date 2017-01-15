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

def avoid_self_rating(form, field):
    if field.data == form.rated_by_id.data:
        raise ValidationError('You may not rate yourself!')

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
    dispute_id = RadioField('Choose job')

class AcceptForm(Form):
    deliverable_id = RadioField('Deliverables')

class ResolveForm(Form):
    resolution = TextAreaField('Resolution', validators = [Required()])
    client_payment_amount = TextField('Client payment amount', validators = [Required()])
    dispute_id = RadioField('Disputes')

class AcceptResolutionForm(Form):
    resolution_id = RadioField('Resolution')

class RatingForm(Form):
    rating_choices = [
        ('0', 'Could not have been worse'),
        ('1', 'Bad'),
        ('2', 'Acceptable'),
        ('3', 'Good'),
        ('4', 'Very good'),
        ('5', 'Could not have been better')
    ]
    job_id = TextField('Job id', validators = [Required()], default='')
    user_id = TextField('User SIN', validators = [Required(), avoid_self_rating], default='')
    rated_by_id = TextField('Rated by SIN', validators = [Required()], default='')
    rating = RadioField('Rate user\'s performance', choices=rating_choices, validators=[Required()], default=0)
    comments = TextAreaField('Comments', validators = [], default='')