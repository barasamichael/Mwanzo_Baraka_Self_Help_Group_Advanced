from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import (ValidationError, StringField, IntegerField, FloatField, FileField, 
        SelectField, SubmitField, PasswordField)
from wtforms.validators import DataRequired, Length, Email
from ..models import member, document, phone_number, month, occupation, employer

class LoginMemberForm(FlaskForm):
    email_address = StringField('Email',
            validators=[DataRequired(), Length(1, 128), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class EmploymentForm(FlaskForm):
    employer_id = SelectField('select employer', validators = [DataRequired()])
    occupation_id = SelectField('select occupation', validators = [DataRequired()])

    submit = SubmitField('submit')


class RegisterOccupationForm(FlaskForm):
    description = StringField('description', validators = [DataRequired(),Length(1, 255)])
    submit = SubmitField('submit')

    def validate_description(self, field):
        if occupation.query.filter_by(description = field.data).first():
            raise ValidationError('Occupation already registered.')


class RegisterEmployerForm(FlaskForm):
    name = StringField('employer name', validators = [DataRequired(), Length(1, 255)])
    email_address = StringField('email address', 
            validators = [DataRequired(), Length(1, 255), Email()])
    
    phone_no = StringField('phone number', validators = [DataRequired(), Length(1, 13)])
    
    location_address = StringField('location address', 
            validators = [DataRequired(), Length(1, 255)])

    submit = SubmitField('submit')

    def validate_email_address(self, field):
        if employer.query.filter_by(email_address = field.data).first():
            raise ValidationError('Email address is already in use.')

    def validate_name(self, field):
        if employer.query.filter_by(name = field.data).first():
            raise ValidationError('Employer with the same name is already registered.')


class RegisterMonthlyDepositForm(FlaskForm):
    description = StringField('description', 
            validators = [DataRequired(), Length(1, 64)])
    submit = SubmitField('submit')

    def validate_description(self, field):
        if month.query.filter_by(description = field.data).first():
            raise ValidationError('Monthly deposit already registered.')


class RegisterLoanTypeForm(FlaskForm):
    description = StringField('description', validators = [DataRequired(),Length(1, 255)])
    rate = FloatField('interest rate per month', validators = [DataRequired()])
    max_period = IntegerField('maximum repayment period in years', 
            validators = [DataRequired()])
    multiplier = FloatField('loan multiplier', validators = [DataRequired()])
    overdue_penalty = FloatField('overdue penalty rate', validators = [DataRequired()])

    submit = SubmitField('submit')


class RegisterDocumentTypeForm(FlaskForm):
    description = StringField('Document description', 
            validators = [DataRequired(), Length(1, 255)])
    submit = SubmitField('submit')


class RegisterPhoneNoForm(FlaskForm):
    phone_no = StringField('Phone number', validators = [DataRequired(), Length(1, 13)])
    submit = SubmitField('submit')

    def validate_phone_no(self, field):
        if phone_number.query.filter_by(phone_no = field.data).first():
            raise ValidationError('phone number is already in use')

class LoanForm(FlaskForm):
    loan_type = SelectField('type of loan', validators = [DataRequired()])
    amount = IntegerField('amount', validators = [DataRequired()])

    submit = SubmitField('submit')


class RegistrationFeeForm(FlaskForm):
    amount = IntegerField('enter amount', validators = [DataRequired()])
    submit = SubmitField('submit')


class MonthlyDepositForm(FlaskForm):
    month_id = SelectField('select month', validators = [DataRequired()])
    amount = FloatField('amount', validators = [DataRequired()])
    submit = SubmitField('submit')


class DocumentUploadForm(FlaskForm):
    type_id = SelectField('Document type', validators = [DataRequired(), Length(1, 255)])
    file = FileField('Select File', 
            validators = [FileRequired(), FileAllowed(['pdf'], 'Select PDF Files Only.')])
    
    submit = SubmitField('submit')

    def validate_file(self, field):
        if document.query.filter_by(filename = field.data).first():
            raise ValidationError('Document with same filename is already uploaded by you or another user. Change filename for uniqueness.')
