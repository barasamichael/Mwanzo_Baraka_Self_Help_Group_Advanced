from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import (StringField, SelectField, BooleanField, SubmitField, IntegerField, 
        FileField, PasswordField)
from wtforms.validators import DataRequired, Length, Email, EqualTo
from wtforms.fields.html5 import DateField
from wtforms import ValidationError
from flask_login import current_user

from ..models import (member, group, user, loan, loan_type, monthly_deposit, 
        monthly_deposit_overdue, loan_overdue, deposit_overdue_payment, 
        loan_overdue_payment, installment)

class ImageForm(FlaskForm):
    file = FileField('select file', validators = [FileRequired(),
        FileAllowed(['jpg', 'png', 'gif', 'jpeg'], 'Select Image Files Only.')])

    submit = SubmitField('submit')


class OverduePaymentForm(FlaskForm):
    amount = IntegerField('enter amount', validators = [DataRequired()])
    submit = SubmitField('submit')

    def validate_amount(self, field):
        if field.data <= 0:
            raise ValidationError('Amount cannot  be zero or less.')

class UpdateOverdueMonthlyDepositsFiltersForm(FlaskForm):
    period = IntegerField('period the operation should span (months)', validators = [DataRequired()])
    submit = SubmitField('submit')

class InstallmentForm(FlaskForm):
    amount = IntegerField('enter amount', validators = [DataRequired()])
    submit = SubmitField('submit')

    def validate_amount(self, field):
        if field.data <= 0:
            raise ValidationError('Amount cannot  be zero or less.')
