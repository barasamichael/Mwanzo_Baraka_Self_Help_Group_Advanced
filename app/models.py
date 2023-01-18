import flask
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as serializer
from datetime import datetime

from . import db, login_manager

#register load_user to be called when info about logged in user is required
@login_manager.user_loader
def load_user(user_id):
    return user.query.get(int(user_id))


class Permission:
    VISIT = 1
    MEMBER = 2
    GROUP_MEMBER = 4
    VIEW = 8
    REGISTER = 16
    MODERATE = 32
    ADMIN = 64


class role(db.Model):
    __tablename__ = 'role'

    role_id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), nullable = False, unique = True)
    default = db.Column(db.Boolean, default = False, index = True)
    permissions = db.Column(db.Integer)

    #relationships
    users = db.relationship('user', backref = 'role', lazy = 'dynamic')

    def __init__(self, **kwargs):
        super(role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
                'Guest' : [Permission.VISIT],
                'Member' : [Permission.VISIT, Permission.MEMBER],
                'Group Member' : [Permission.VISIT, Permission.GROUP_MEMBER, 
                    Permission.MEMBER],
                'Security Personnel' :[Permission.VISIT, Permission.VIEW],
                'Junior Staff' : [Permission.VISIT, Permission.VIEW, Permission.MEMBER, 
                    Permission.REGISTER],
                'Senior Staff' : [Permission.VISIT, Permission.VIEW, Permission.REGISTER,
                    Permission.MODERATE, Permission.MEMBER],
                'Administrator' : [Permission.VISIT, Permission.VIEW, Permission.REGISTER,                     Permission.MODERATE, Permission.ADMIN, Permission.MEMBER]
                }
        
        default_role = 'Guest'

        for r in roles:
            Role = role.query.filter_by(name = r).first()
            if Role is None:
                Role = role(name = r)

            Role.reset_permission()
            for perm in roles[r]:
                Role.add_permission(perm)

            Role.default = (Role.name == default_role)
            db.session.add(Role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permission(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

            
class anonymous_user(AnonymousUserMixin):
    def can(self, permission):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = anonymous_user

class user(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)

    first_name = db.Column(db.String(128), nullable = False)
    middle_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    date_of_birth = db.Column(db.Date, default = datetime.utcnow, nullable = False)

    gender = db.Column(db.String(8), default = 'female', nullable = False)
    email_address = db.Column(db.String(128), nullable = False, unique = True)
    location_address = db.Column(db.String(255), nullable = False)
    nationality = db.Column(db.String(128), default = "Kenya", nullable = False)
    id_no = db.Column(db.Integer, nullable = False, unique = True)
    associated_image= db.Column(db.String(255))

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default = False)
    active = db.Column(db.Boolean, default = True)

    #relationships
    role_id = db.Column(db.Integer, db.ForeignKey('role.role_id'))

    def __init__(self,**kwargs):
        super(user, self). __init__(**kwargs)
        if self.role_id is None:
            if self.email_address == flask.current_app.config['FLASKY_ADMIN_EMAIL']:
                Role = role.query.filter_by(name = 'Administrator').first()
                self.role_id = Role.role_id

            if self.role_id is None:
                Role = role.query.filter_by(default = True).first()
                self.role_id = Role.role_id

    def can(self, perm):
        Role = role.query.filter_by(role_id = self.role_id).first()

        return self.role_id is not None and Role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration = 3600):
        s = serializer(flask.current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm' : self.id}).decode('utf-8')

    def confirm(self, token):
        s = serializer(flask.current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False

        if data.get('confirm') != self.id:
            return False

        self.confirmed = True
        db.session.add(self)

        return True


class member(db.Model):
    __tablename__ = "member"
    member_id = db.Column(db.Integer, primary_key = True, nullable = False)

    first_name = db.Column(db.String(128), nullable = False)
    middle_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    date_of_birth = db.Column(db.Date, default = datetime.utcnow, nullable = False)

    gender = db.Column(db.String(8), default = 'female', nullable = False)
    email_address = db.Column(db.String(128), nullable = False, unique = True)
    location_address = db.Column(db.String(255), nullable = False)
    nationality = db.Column(db.String(128), default = "Kenya", nullable = False)
    id_no = db.Column(db.Integer, nullable = False, unique = True)
    associated_image = db.Column(db.String(255))

    status = db.Column(db.String(16), default = "deactivated", nullable = False)
    logged_in = db.Column(db.Boolean, default = False)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow, 
            onupdate = datetime.utcnow)

    #relationships
    group_id = db.Column(db.Integer, db.ForeignKey('group.group_id'))

    documents = db.relationship('document', backref = 'owner', lazy = 'dynamic')
    deposits = db.relationship('monthly_deposit', backref = 'owner', lazy = 'dynamic')
    fees = db.relationship('registration_fee', backref = 'owner', lazy = 'dynamic')
    phone_nos = db.relationship('phone_number', backref = 'owner', lazy = 'dynamic')
    emails = db.relationship('email_received', backref = 'owner', lazy = 'dynamic')
    loans = db.relationship('loan', backref = 'owner', lazy = 'dynamic')
    reviews = db.relationship('review', backref = 'owner', lazy = 'dynamic')
    overdue_deposits = db.relationship('monthly_deposit_overdue', backref = 'owner', lazy = 'dynamic')
    
    def __repr__(self):
        return '<Member %r>' % self.first_name


class group(db.Model):
    __tablename__ = "group"
    group_id = db.Column(db.Integer, primary_key = True, nullable = False)

    name = db.Column(db.String(255), nullable = False, unique = True)
    email_address = db.Column(db.String(255), nullable = False, unique = True)
    phone_no = db.Column(db.String(16), nullable = False, unique = True)
    location_address = db.Column(db.String(255), nullable = False)
    associated_image = db.Column(db.String(255))

    active = db.Column(db.Boolean, default = True)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    members = db.relationship('member', backref = 'group', lazy = 'dynamic')

    def __repr__(self):
        return '<Group : %r>' % self.name

class review(db.Model):
    __tablename__ = 'review'
    review_id = db.Column(db.Integer, primary_key = True, index = True)
    description = db.Column(db.Text, nullable = True)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id'), nullable = False)


class document_type(db.Model):
    __tablename__ = "document_type"
    type_id = db.Column(db.Integer, primary_key = True, nullable = False)

    description = db.Column(db.String(255), nullable = False)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    documents = db.relationship('document', backref = 'type', lazy = 'dynamic')

    def __repr__(self):
        return '<Document Type : %r>' % self.description


class document(db.Model):
    __tablename__ = "document"
    document_id = db.Column(db.Integer, primary_key = True, nullable = False)

    filename = db.Column(db.String(255), nullable = False, unique = True)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id'))
    type_id = db.Column(db.Integer, db.ForeignKey('document_type.type_id'))

    def __repr__(self):
        return '<Document : %r>' % self.filename


class month(db.Model):
    __tablename__ = 'month'

    month_id = db.Column(db.Integer, primary_key = True, nullable = False)
    description = db.Column(db.String(64), nullable = False, index = True, unique = True)

    #relationships
    deposits = db.relationship('monthly_deposit', backref = 'month', lazy = 'dynamic')
    overdues = db.relationship('monthly_deposit_overdue', backref = 'month', lazy = 'dynamic')
    
    def __repr__(self):
        return '<Month : %r>' % self.description


class monthly_deposit(db.Model):
    __tablename__ = "monthly_deposit"
    deposit_id = db.Column(db.Integer, primary_key = True, nullable = False)

    amount = db.Column(db.Integer, nullable = False)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id'))
    month_id = db.Column(db.Integer, db.ForeignKey('month.month_id'))

    def __repr__(self):
        return '<Deposit : %r>' % self.amount


class loan_type(db.Model):
    __tablename__ = "loan_type"
    loan_type_id = db.Column(db.Integer, primary_key = True, nullable = False)

    description = db.Column(db.String(255), nullable = False, unique = True)
    rate = db.Column(db.Float, nullable = False)
    max_period = db.Column(db.Integer, nullable = False)
    multiplier = db.Column(db.Float, nullable = False)
    overdue_penalty = db.Column(db.Float, nullable = False)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    loans = db.relationship('loan', backref='type', lazy='dynamic')

    def __repr__(self):
        return '<Loan Type : %r>' % self.descriptiom


class registration_fee(db.Model):
    __tablename__ = "registration_fee"
    fee_id = db.Column(db.Integer, primary_key = True, nullable = False)

    amount = db.Column(db.Integer, nullable = False)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id'))

    def __repr__(self):
        return '<Registration Fee : %r>' % self.amount


class phone_number(db.Model):
    __tablename__ = "phone_number"
    phone_id = db.Column(db.Integer, primary_key = True, nullable = False)

    phone_no = db.Column(db.String(13), nullable = False, unique = True)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id'))

    def __repr__(self):
        return '<Phone Number : %r>' % self.phone_no


class email_received(db.Model):
    __tablename__ = "email_received"
    email_id = db.Column(db.Integer, primary_key = True, nullable = False)

    subject = db.Column(db.String(255))
    body = db.Column(db.Text, nullable = False)
    html = db.Column(db.Text)

    status = db.Column(db.String(16), default = "unread")

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    attachments = db.relationship('attachment', backref='email', lazy='dynamic')
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id'))

    def __repr__(self):
        return '<Email Received : %r>' % self.subject


class employer(db.Model):
    __tablename__ = "employer"
    employer_id = db.Column(db.Integer, primary_key = True, nullable = False)

    name = db.Column(db.String(255), nullable = False)
    email_address = db.Column(db.String(128), nullable = False, unique = True)
    phone_no = db.Column(db.String(13), nullable = False, unique = True)
    location_address = db.Column(db.String(255), nullable = False)
    status = db.Column(db.String(32), default = 'active', nullable = False)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    employees = db.relationship('employment', backref='employer', lazy='dynamic')

    def __repr__(self):
        return '<Employer : %r>' % self.name


class occupation(db.Model):
    __tablename__ = "occupation"
    occupation_id = db.Column(db.Integer, primary_key = True, nullable = False)

    description = db.Column(db.String(255), nullable = False, unique = True)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    employees = db.relationship('employment', backref='occupation', lazy='dynamic')

    def __repr__(self):
        return '<Occupation : %r>' % self.description


class employment(db.Model):
    __tablename__ = "employment"
    employment_id = db.Column(db.Integer, primary_key = True, nullable = False)

    status = db.Column(db.String(16), default = "active", nullable = False)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id'))
    occupation_id = db.Column(db.Integer, db.ForeignKey('occupation.occupation_id'))
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.employer_id'))

    def __repr__(self):
        return '<Employment : %r>' % self.employment_id


class attachment(db.Model):
    __tablename__ = "attachment"
    attachment_id = db.Column(db.Integer, primary_key = True, nullable = False)

    filename = db.Column(db.String(255), nullable = False, unique = True)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    email_id = db.Column(db.Integer, db.ForeignKey('email_received.email_id'))

    def __repr__(self):
        return '<Attachment : %r>' % self.filename


class loan(db.Model):
    __tablename__ = 'loan'
    loan_id = db.Column(db.Integer, primary_key = True, nullable = False)

    amount = db.Column(db.Integer, nullable = False)
    status = db.Column(db.String(16), default = "pending", nullable = False)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id'))
    loan_type = db.Column(db.Integer, db.ForeignKey('loan_type.loan_type_id'))

    installments = db.relationship('installment', backref = 'loan', lazy = 'dynamic')

    def __repr__(self):
        return '<Loan %r>' % self.amount


class installment(db.Model):
    __tablename__ = 'installment'
    installment_id = db.Column(db.Integer, primary_key = True)
    
    amount = db.Column(db.Integer, nullable = False)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationship
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.loan_id'), nullable = False)

    def __repr__(self, field):
        return '<Installment ID %r>'% field.data


class loan_overdue(db.Model):
    __tablename__ = 'loan_overdue'
    loan_overdue_id = db.Column(db.Integer, primary_key = True)
    
    amount = db.Column(db.Integer, nullable = False)
    month = db.Column(db.String(32), nullable = False)
    status = db.Column(db.String(16), default = "pending")
    
    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationship
    loan_id =  db.Column(db.Integer, db.ForeignKey('loan.loan_id'), nullable = False)
    
    payments = db.relationship('loan_overdue_payment', backref = 'overdue',  
            lazy = 'dynamic')

    def __repr__(self):
        return '<Loan Overdue ID %r>' % self.loan_overdue_id


class loan_overdue_payment(db.Model):
    __tablename__ = 'loan_overdue_payment'
    loan_overdue_payment_id = db.Column(db.Integer, primary_key = True)
    
    amount = db.Column(db.Integer, nullable = False)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    loan_overdue_id = db.Column(db.Integer, db.ForeignKey('loan_overdue.loan_overdue_id'),
            nullable = False)

    def __repr__(self):
        return ''% self.loan_overdue_payment_id


class monthly_deposit_overdue(db.Model):
    __tablename__ = 'monthly_deposit_overdue'
    monthly_deposit_overdue_id = db.Column(db.Integer, primary_key = True)
    
    amount = db.Column(db.Integer, nullable = False)
    status = db.Column(db.String(16), default = "pending")

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationship
    month_id = db.Column(db.Integer, db.ForeignKey('month.month_id'), nullable = False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.member_id'), nullable = False)

    payments = db.relationship('deposit_overdue_payment', backref = 'overdue', 
            lazy = 'dynamic')

    def __repr__(self):
        return '<Monthly deposit Overdue ID : %r>'% self.monthly_deposit_overdue_id


class deposit_overdue_payment(db.Model):
    __tablename__ = 'deposit_overdue_payment'
    deposit_overdue_payment_id = db.Column(db.Integer, primary_key = True)

    amount = db.Column(db.Integer, nullable = False)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    monthly_deposit_overdue_id = db.Column(db.Integer, 
            db.ForeignKey('monthly_deposit_overdue.monthly_deposit_overdue_id'), 
            nullable = False)


class event(db.Model):
    __tablename__ = 'event'
    event_id = db.Column(db.Integer, primary_key = True, index = True)
    description = db.Column(db.String(255), nullable = False, unique = True)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    images = db.relationship('event_image', backref = 'event', lazy = 'dynamic')

    def __repr__(self):
        return '< Event : %r>'%self.description


class event_image(db.Model):
    __tablename__ = 'event_image'
    image_id = db.Column(db.Integer, primary_key = True, nullable = False)
    description = db.Column(db.String(255), nullable = False)

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    #relationships
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id'), nullable = False)

    def __repr__(self):
        return '<Image : %r>'%self.description


class branch(db.Model):
    __tablename__ = 'branch'
    branch_id = db.Column(db.Integer, primary_key = True)

    town = db.Column(db.String(64), nullable = False)
    location_address = db.Column(db.String(255), nullable = False)
    phone_no = db.Column(db.String(16), nullable = False)
    email_address = db.Column(db.String(128), nullable = False)
    associated_image = db.Column(db.String(255))

    date_created = db.Column(db.DateTime, default = datetime.utcnow)
    last_updated = db.Column(db.DateTime, default = datetime.utcnow,
            onupdate = datetime.utcnow)

    def __repr__(self):
        return '<Branch : %r>'% self.town
