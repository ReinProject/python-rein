from flask import Flask, request
from flask_wtf import Form
from wtforms import TextField, TextAreaField, RadioField
from wtforms.validators import Required

from mediator import get_mediators

class JobPostForm(Form):
    mediators = get_mediators(rein, user, urls, log)
    job_name = TextField('Job name', validators = [Required()])
    description = TextAreaField('Description', validators = [Required()])
    tags = TextField('Tags', validators = [Required()])
    expire_days = TextField('Expiration (days)', validators = [Required()])
    mediator_pubkey = RadioField('Choose mediator', choices = ['option1'] ) #mediator_pubkeys)
