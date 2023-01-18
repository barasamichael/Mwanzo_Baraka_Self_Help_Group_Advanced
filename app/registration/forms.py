from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import (StringField, SelectField, BooleanField, SubmitField, IntegerField, 
        FileField, PasswordField)
from wtforms.validators import DataRequired, Length, Email, EqualTo
from wtforms.fields.html5 import DateField
from wtforms import ValidationError
from flask_login import current_user
from ..models import member, group, user, event, branch


class ImageForm(FlaskForm):
    file = FileField('select file', validators = [FileRequired(),
        FileAllowed(['jpg', 'png', 'gif', 'jpeg'], 'Select Image Files Only.')])

    submit = SubmitField('submit')


class RegisterEventForm(FlaskForm):
    description = StringField('description', validators = [DataRequired(),Length(1, 255)])
    submit = SubmitField('submit')

    def validate_description(self, field):
        if event.query.filter_by(description = field.data).first():
            raise ValidationError(f'Event {field.data} already exists.')


class RegisterBranchForm(FlaskForm):
    town = StringField('Town', validators = [DataRequired(), Length(1, 64)])
    phone_no = StringField('Phone Number', validators = [DataRequired(), Length(1, 16)])
    email_address = StringField('Email Address',
            validators = [DataRequired(), Length(1, 128), Email()])
    location_address = StringField('Location Address', 
            validators = [DataRequired(), Length(1, 255)])

    submit = SubmitField('submit')

    def validate_town(self,field):
        if branch.query.filter_by(town = field.data).first():
            raise ValidationError(f'{field.data} Branch already registered.')

    def validate_location_address(self,field):
        if branch.query.filter_by(location_address = field.data).first():
            raise ValidationError(f'{field.data} already exists')

    def validate_phone_no(self,field):
        if branch.query.filter_by(phone_no= field.data).first():
            raise ValidationError(f'{field.data} already exists.')

    def validate_email_address(self,field):
        if branch.query.filter_by(email_address = field.data).first():
            raise ValidationError(f'{field.data} already exists.')


class UpdateMemberProfileForm(FlaskForm):
    id_no = IntegerField('national ID number', validators = [DataRequired()])
    first_name = StringField('first name', validators = [DataRequired(), Length(1, 128)])
    middle_name = StringField('middle name', validators = [DataRequired(),Length(1, 128)])
    last_name = StringField('last name', validators = [Length(0, 128)])

    date_of_birth = DateField('date of birth', validators = [DataRequired()])
    gender = SelectField('gender', choices = [('male', 'male'), ('female', 'female')],
            validators = [DataRequired(), Length(1, 16)])

    location_address = StringField('location address',
            validators = [DataRequired(), Length(1, 255)])

    nationality = SelectField('nationality', validators = [DataRequired(),Length(1, 128)])

    submit = SubmitField('submit')


class UpdateUserProfileForm(FlaskForm):
    id_no = IntegerField('national ID number', validators = [DataRequired()])
    first_name = StringField('first name', validators = [DataRequired(), Length(1, 128)])
    middle_name = StringField('middle name', validators = [Length(0, 128)])
    last_name = StringField('last name', validators = [Length(0, 128)])

    date_of_birth = DateField('date of birth', validators = [DataRequired()])
    gender = SelectField('gender', choices = [('male', 'male'), ('female', 'female')],
            validators = [DataRequired(), Length(1, 16)])

    location_address = StringField('location address',
            validators = [DataRequired(), Length(1, 255)])

    nationality = SelectField('nationality', validators = [DataRequired(),Length(1, 128)])

    submit = SubmitField('submit')

    def validate_id_no(self, field):
        if user.query.filter_by(id_no = field.data).first() != current_user:
            raise ValidationError('National ID number is already in use.')


class RegisterUserForm(FlaskForm):
    id_no = IntegerField('national ID number', validators = [DataRequired()])
    first_name = StringField('first name', validators = [DataRequired(), Length(1, 128)])
    middle_name = StringField('middle name', validators = [Length(0, 128)])
    last_name = StringField('last name', validators = [Length(0, 128)])

    gender = SelectField('gender', choices = [('male', 'male'), ('female', 'female')],
            validators = [DataRequired(), Length(1, 16)])

    date_of_birth = DateField('date of birth', validators = [DataRequired()])

    email_address = StringField('email address',
            validators = [DataRequired(), Length(1, 128), Email()])

    location_address = StringField('location address',
            validators = [DataRequired(), Length(1, 255)])

    nationality = SelectField('nationality', validators = [DataRequired(),Length(1, 128)])
    
    password = PasswordField('password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('confirm password', validators=[DataRequired()])
    
    submit = SubmitField('submit')

    def validate_email_address(self, field):
        if user.query.filter_by(email_address = field.data).first():
            raise ValidationError('Email address is already in use.')

    def validate_id_no(self, field):
        if user.query.filter_by(id_no = field.data).first():
            raise ValidationError('National ID number is already in use.')

class UpdateGroupProfileForm(FlaskForm):
    name = StringField('group name', validators = [DataRequired(), Length(1, 128)])
    location_address = StringField('location address',
            validators = [DataRequired(), Length(1, 255)])

    submit = SubmitField('submit')


class RegisterGroupForm(FlaskForm):
    name = StringField('group name', validators = [DataRequired(), Length(1, 128)])
    email_address = StringField('email address', 
            validators = [DataRequired(), Length(1, 128), Email()])
    phone_no = StringField('phone number', validators = [DataRequired(), Length(1, 14)])
    location_address = StringField('location address',
            validators = [DataRequired(), Length(1, 255)])

    submit = SubmitField('submit')

    def validate_email_address(self, field):
        if group.query.filter_by(email_address = field.data).first():
            raise ValidationError('Email address is already in use.')

    def validate_phone_no(self, field):
        if group.query.filter_by(email_address = field.data).first():
            raise ValidationError('Phone number is already in use.')


class RegisterMemberForm(FlaskForm):
    id_no = IntegerField('national ID number', validators = [DataRequired()])
    first_name = StringField('first name', validators = [DataRequired(), Length(1, 128)])
    middle_name = StringField('middle name', validators = [DataRequired(),Length(1, 128)])
    last_name = StringField('last name', validators = [Length(0, 128)])

    gender = SelectField('gender', choices = [('male', 'male'), ('female', 'female')], 
            validators = [DataRequired(), Length(1, 16)])

    email_address = StringField('email address', 
            validators = [DataRequired(), Length(1, 128), Email()])

    location_address = StringField('location address', 
            validators = [DataRequired(), Length(1, 255)])

    nationality = SelectField('nationality', validators = [DataRequired(),Length(1, 128)])
    
    submit = SubmitField('submit')

    def validate_email_address(self, field):
        if member.query.filter_by(email_address = field.data).first():
            raise ValidationError('Email address is already in use.')

    def validate_id_no(self, field):
        if member.query.filter_by(id_no = field.data).first():
            raise ValidationError('National ID number is already in use.')
