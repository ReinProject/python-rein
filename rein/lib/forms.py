from flask import Flask
from flask_wtf import Form
from wtforms import TextField, TextAreaField, RadioField, PasswordField
from wtforms.validators import Required, ValidationError
from wtforms.widgets import HiddenInput
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
        raise ValidationError(_("Not a valid private key."))

def validate_address(form, field):
    if not check_bitcoin_address(field.data):
        raise ValidationError(_("Invalid address"))

def validate_en(form, field):
    message = field.data.replace("\r\n","\n")
    if not validate_enrollment(message):
        raise ValidationError(_("Invalid signature"))

def validate_mediator_fee(form, field):
    try:
        float(field.data)
    except ValueError:
        raise ValidationError("Invalid mediator fee")

def avoid_self_rating(form, field):
    if field.data == form.rated_by_id.data:
        raise ValidationError('You may not rate yourself!')

class SetupForm(Form):
    name = TextField(_('Name / Handle'), validators = [Required()])
    contact = TextField(_('Email / Bitmessage'), validators = [Required()])
    maddr = TextField(_('Master Bitcoin address'), validators = [Required(), validate_address])
    daddr = TextField(_('Delegate Bitcoin address'), validators = [Required(), validate_address])
    dkey = PasswordField(_('Delegate Bitcoin private Key'), validators = [Required(), validate_privkey])
    will_mediate = RadioField(_('Register as a mediator?'), choices = [('1','Yes'), ('0', 'No')])
    mediator_fee = TextField(_('Mediator Fee'), validators = [validate_mediator_fee])  # TODO make required only if Yes above

class SignForm(Form):
    identity_id = HiddenInput("identity_id")
    signed = TextAreaField(_('Signed enrollment'), validators = [Required(), validate_en])

class JobPostForm(Form):
    job_name = TextField(_('Job name'), validators = [Required()])
    description = TextAreaField(_('Description'), validators = [Required()])
    tags = TextField(_('Tags'), validators = [Required()])
    expire_days = TextField(_('Expiration (days)'), validators = [Required()])
    mediator_maddr = RadioField(_('Choose mediator'))

class BidForm(Form):
    description = TextAreaField(_('Description'), validators = [Required()])
    bid_amount = TextAreaField(_('Bid amount'), validators = [Required()])
    job_id = RadioField(_('Choose Job to bid on'))

class JobOfferForm(Form):
    bid_id = RadioField(_('Choose bid'))

class DeliverForm(Form):
    deliverable = TextAreaField(_('Deliverables'), validators = [Required()])
    job_id = RadioField(_('Choose job associated with deliverables'))

class DisputeForm(Form):
    dispute_detail = TextAreaField(_('Dispute detail'), validators = [Required()])
    order_id = RadioField(_('Choose job'))

class AcceptForm(Form):
    deliverable_id = RadioField(_('Deliverables'))

class ResolveForm(Form):
    resolution = TextAreaField(_('Resolution'), validators = [Required()])
    client_payment_amount = TextField(_('Client payment amount in BTC (remainder sent to worker)'), validators = [Required()])
    dispute_id = RadioField(_('Disputes'))

class AcceptResolutionForm(Form):
    resolution_id = RadioField(_('Resolution'))

class RatingForm(Form):
    job_id = TextField(_('Select job'), validators = [Required()], default='')
    user_id = TextField(_('Select user'), validators = [Required(), avoid_self_rating], default='')
    rated_by_id = TextField(_('Your SIN'), validators = [Required()], default='')
    rating = TextField(_('Rating'), validators=[Required()], default=1, widget=HiddenInput())
    comments = TextAreaField(_('Comments'), validators = [], default='')
