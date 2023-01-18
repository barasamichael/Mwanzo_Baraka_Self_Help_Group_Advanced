import flask, os
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required

from . import profiles
from .forms import (RegisterDocumentTypeForm, DocumentUploadForm, RegisterPhoneNoForm, 
        RegisterLoanTypeForm, RegistrationFeeForm, LoanForm, RegisterMonthlyDepositForm, 
        MonthlyDepositForm, RegisterEmployerForm, EmploymentForm, RegisterOccupationForm,
        LoginMemberForm)

from .. import db
from ..decorators import permission_required
from ..models import (user, member, group, document_type, document, phone_number, 
        loan_type, loan, registration_fee, month, monthly_deposit, employer, employment, 
        occupation, role, Permission)


@profiles.route('/view_loans')
@login_required
@permission_required(Permission.REGISTER)
def view_loans():
    page = flask.request.args.get('page', 1, type = int)
    pagination = loan.query.join(member, member.member_id == loan.member_id)\
            .join(loan_type, loan_type.loan_type_id == loan.loan_type)\
            .add_columns(
                    loan.loan_id,
                    loan.amount,
                    loan.date_created,
                    loan.status,
                    member.member_id,
                    member.first_name,
                    member.middle_name,
                    member.last_name,
                    loan_type.loan_type_id,
                    loan_type.description
                ).order_by(loan.loan_id.desc()).paginate(page,
                        per_page = flask.current_app.config['FLASKY_POSTS_PER_PAGE'], 
                        error_out = False)
    loans = pagination.items
    return flask.render_template('profiles/view_loans.html', loans = loans, 
            pagination = pagination)


@profiles.route('/view_monthly_deposits')
@login_required
@permission_required(Permission.REGISTER)
def view_monthly_deposits():
    page = flask.request.args.get('page', 1, type = int)
    pagination = monthly_deposit.query\
            .join(month, month.month_id == monthly_deposit.month_id)\
            .join(member, member.member_id == monthly_deposit.member_id)\
            .add_columns(
                    member.member_id,
                    member.first_name,
                    member.middle_name,
                    member.last_name,
                    monthly_deposit.deposit_id,
                    monthly_deposit.amount,
                    monthly_deposit.date_created,
                    month.month_id,
                    month.description
                    ).order_by(monthly_deposit.deposit_id.desc())\
            .paginate(page, per_page = flask.current_app.config['FLASKY_POSTS_PER_PAGE'], 
                    error_out = False)
    
    deposits = pagination.items
    return flask.render_template('profiles/view_monthly_deposits.html', 
            deposits = deposits, pagination = pagination)


@profiles.route('/view_registration_fees')
@login_required
@permission_required(Permission.REGISTER)
def view_registration_fees():
    page = flask.request.args.get('page', 1, type = int)
    pagination = registration_fee.query\
            .join(member, member.member_id == registration_fee.member_id)\
            .add_columns(
                    registration_fee.amount,
                    registration_fee.fee_id,
                    registration_fee.date_created,
                    member.member_id,
                    member.first_name,
                    member.middle_name,
                    member.last_name
                    ).order_by(registration_fee.fee_id.desc())\
            .paginate(page, per_page = flask.current_app.config['FLASKY_POSTS_PER_PAGE'], 
                    error_out = False)
    fees = pagination.items

    return flask.render_template('profiles/view_registration_fees.html', fees = fees, 
            pagination = pagination)


@profiles.route('/login_member', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MEMBER)
def login_member():
    form = LoginMemberForm()

    if form.validate_on_submit():
        Member = member.query.filter_by(email_address = form.email_address.data).first()

        if Member:
            return flask.redirect(
                flask.url_for('profiles.member_profile', member_id = Member.member_id))
        
        flask.flash('Invalid Credentials.')
    return flask.render_template('profiles/login_member.html', form = form)


@profiles.route('/employer_profile/<int:employer_id>')
@login_required
@permission_required(Permission.REGISTER)
def employer_profile(employer_id):
    Employer = employer.query.filter_by(employer_id = employer_id).first_or_404()

    page = flask.request.args.get('page', 1, type = int)
    pagination = employment.query.filter_by(employer_id = employer_id)\
            .join(occupation, occupation.occupation_id == employment.occupation_id)\
            .join(member, member.member_id == employment.member_id)\
            .add_columns(
                    employment.employment_id,
                    employment.status,
                    occupation.occupation_id,
                    occupation.description,
                    member.member_id,
                    member.first_name,
                    member.middle_name,
                    member.last_name,
                    member.gender
                    )\
            .paginate(page, flask.current_app.config['FLASKY_POSTS_PER_PAGE'], 
                    error_out = False)
    
    employees = pagination.items
    return flask.render_template('profiles/employer_profile.html', employer = Employer, 
            employees = employees, pagination = pagination)


@profiles.route('/occupation_details/<int:occupation_id>')
@login_required
@permission_required(Permission.REGISTER)
def occupation_details(occupation_id):
    Occupation = occupation.query.filter_by(occupation_id = occupation_id).first_or_404()

    page = flask.request.args.get('page', 1, type = int)
    pagination = employment.query.filter_by(occupation_id = occupation_id)\
            .join(occupation, occupation.occupation_id == employment.occupation_id)\
            .join(member, member.member_id == employment.member_id)\
            .join(employer, employer.employer_id == employment.employer_id)\
            .add_columns(
                    employer.employer_id,
                    employer.name,
                    employment.employment_id,
                    employment.status,
                    member.member_id,
                    member.first_name,
                    member.middle_name,
                    member.last_name,
                    member.gender,
                    occupation.occupation_id,
                    occupation.description)\
            .paginate(page, per_page = flask.current_app.config['FLASKY_POSTS_PER_PAGE'], 
                    error_out = False)
    
    members = pagination.items
    
    return flask.render_template('profiles/occupation_details.html', 
            occupation = Occupation, members = members, pagination = pagination)


@profiles.route('/view_occupations')
@login_required
@permission_required(Permission.REGISTER)
def view_occupations():
    page = flask.request.args.get('page', 1, type = int)
    pagination = occupation.query.order_by(occupation.description.desc())\
            .paginate(page, flask.current_app.config['FLASKY_POSTS_PER_PAGE'],
                    error_out = False
            )
    occupations = pagination.items

    return flask.render_template('profiles/view_occupations.html', pagination=pagination,
            occupations = occupations)

    
@profiles.route('/register_occupation', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def register_occupation():
    form = RegisterOccupationForm()

    if form.validate_on_submit():
        Occupation = occupation(description = form.description.data)
        db.session.add(Occupation)
        db.session.commit()

        flask.flash(f'{form.description.data} registered successfully.')
        return flask.redirect(
                flask.url_for('profiles.user_profile'))

    return flask.render_template('profiles/register_occupation.html', form = form)


@profiles.route('/view_loan_types')
def view_loan_types():
    loan_types = loan_type.query.all()
    return flask.render_template('profiles/view_loan_types.html', loan_types = loan_types)


@profiles.route('/update_loan_type/<int:type_id>', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE)
def update_loan_type(type_id):
    Loan_Type = loan_type.query.filter_by(loan_type_id = type_id).first_or_404()

    form = RegisterLoanTypeForm()

    if form.validate_on_submit():
        Loan_Type.description = form.description.data
        Loan_Type.multiplier = form.multiplier.data
        Loan_Type.max_period = form.max_period.data
        Loan_Type.rate = form.rate.data
        Loan_Type.overdue_penalty = form.overdue_penalty.data

        db.session.add(Loan_Type)
        db.session.commit()

        flask.flash('Update successful.')
        return flask.redirect(flask.url_for('profiles.view_loan_types'))

    form.description.data = Loan_Type.description
    form.multiplier.data = Loan_Type.multiplier
    form.rate.data = Loan_Type.rate
    form.max_period.data = Loan_Type.max_period
    form.overdue_penalty.data = Loan_Type.overdue_penalty

    return flask.render_template('profiles/register_loan_type.html', form = form)


@profiles.route('/view_employers')
@login_required
@permission_required(Permission.REGISTER)
def view_employers():
    page = flask.request.args.get('page', 1, type = int)
    
    pagination = employer.query.order_by(employer.name.desc()).paginate(page,
            flask.current_app.config['FLASKY_POSTS_PER_PAGE'], error_out = False)
    employers = pagination.items

    return flask.render_template('profiles/view_employers.html', employers = employers, 
            pagination = pagination)


@profiles.route('/register_employer', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def register_employer():
    form = RegisterEmployerForm()

    if form.validate_on_submit():
        Employer = employer(
                name = form.name.data,
                email_address = form.email_address.data,
                phone_no = form.phone_no.data,
                location_address = form.location_address.data
                )
        db.session.add(Employer)
        db.session.commit()

        flask.flash(f'{form.name.data} registered successfully.')
        return flask.redirect(flask.url_for('profiles.user_profile'))

    return flask.render_template('profiles/register_employer.html', form = form)

@profiles.route('/register_loan_type', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def register_loan_type():
    form = RegisterLoanTypeForm()
    if form.validate_on_submit():
        Loan_type = loan_type(
                description = form.description.data,
                rate = form.rate.data,
                max_period = form.max_period.data,
                multiplier = form.multiplier.data,
                overdue_penalty = form.overdue_penalty.data
                )
        db.session.add(Loan_type)
        db.session.commit()

        flask.flash('Loan type registered successfully.')
        return flask.redirect(flask.url_for('profiles.user_profile'))

    return flask.render_template('profiles/register_loan_type.html', form = form)


@profiles.route('/register_monthly_deposit', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE)
def register_monthly_deposit():
    form = RegisterMonthlyDepositForm()

    if form.validate_on_submit():
        Month = month(
                description = form.description.data
                )
        db.session.add(Month)
        db.session.commit()

        flask.flash(f'{form.description.data} added successfully.')
        return flask.redirect(flask.url_for('profiles.user_profile'))

    return flask.render_template('profiles/register_monthly_deposit.html', form = form)


@profiles.route('/register_document_type', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def register_document_type():
    form = RegisterDocumentTypeForm()
    if form.validate_on_submit():
        Document_Type = document_type(
                description = form.description.data
        )
        db.session.add(Document_Type)
        db.session.commit()

        flask.flash('Registration successful.')
        return flask.redirect(flask.url_for('profiles.user_profile'))

    return flask.render_template('profiles/register_document_type.html', form = form)


@profiles.route('/personal/<int:member_id>')
@login_required
@permission_required(Permission.MEMBER)
def personal(member_id):
    response = flask.make_response(
        flask.redirect(flask.url_for('profiles.member_profile', member_id = member_id)))
    response.set_cookie('tab_var', '0', max_age = 60*60)
    return response


@profiles.route('/registration_fees/<int:member_id>')
@login_required
@permission_required(Permission.MEMBER)
def registration_fees(member_id):
    response = flask.make_response(flask.redirect(
        flask.url_for('profiles.member_profile', member_id = member_id)))
    response.set_cookie('tab_var', '1', max_age = 60*60)
    return response


@profiles.route('/monthly_deposits/<int:member_id>')
@login_required
@permission_required(Permission.MEMBER)
def monthly_deposits(member_id):
    response = flask.make_response(
        flask.redirect(flask.url_for('profiles.member_profile', member_id = member_id)))
    response.set_cookie('tab_var', '2', max_age = 60*60)
    return response


@profiles.route('/loans/<int:member_id>')
@login_required
@permission_required(Permission.MEMBER)
def loans(member_id):
    response = flask.make_response(
        flask.redirect(flask.url_for('profiles.member_profile', member_id = member_id)))
    response.set_cookie('tab_var', '3', max_age = 60*60)
    return response


@profiles.route('/employment/<int:member_id>')
@login_required
@permission_required(Permission.MEMBER)
def employment_1(member_id):
    response = flask.make_response(
        flask.redirect(flask.url_for('profiles.member_profile', member_id = member_id)))
    response.set_cookie('tab_var', '4', max_age = 60*60)
    return response


@profiles.route('/member_profile/<int:member_id>', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MEMBER)
def member_profile(member_id):
    if current_user.is_anonymous:
        return flask.redirect(flask.url_for('main.homepage'))

    Member = member.query.filter_by(member_id = member_id).first_or_404()
    Group = group.query.filter_by(group_id = Member.group_id).first()

    tab_variable = 0
    if flask.request.cookies.get('tab_var') is not None:
        tab_variable = int(flask.request.cookies.get('tab_var'))

    #personal details
    if tab_variable == 0:
        #extract documents uploaded by member
        documents = document.query.filter_by(member_id = member_id)\
                .join(document_type, document_type.type_id == document.type_id)\
                .add_columns(
                        document_type.type_id,
                        document_type.description,
                        document.document_id,
                        document.filename
                        ).all()
        phone_nos = phone_number.query.filter_by(member_id = member_id).all()

        #form for uploading more documents
        doc_form = DocumentUploadForm()
        contact_form = RegisterPhoneNoForm()
        
        doc_types = document_type.query.order_by(document_type.description.desc()).all()
        doc_form.type_id.choices= [((doc.type_id),(doc.description)) for doc in doc_types]
        
        if doc_form.validate_on_submit():
            uploaded_file = doc_form.file.data
            filename = secure_filename(uploaded_file.filename)

            #save file on server
            uploaded_file.save(os.path.join(
                flask.current_app.config['DOCUMENT_UPLOAD_PATH'], 'members/' + filename))

            #update database
            Document = document(
                    member_id = member_id,
                    type_id = doc_form.type_id.data,
                    filename = filename)
            db.session.add(Document)
            db.session.commit()
            flask.flash('Document added successfully.')

            return flask.redirect(
                    flask.url_for('profiles.personal', member_id = member_id))

        elif contact_form.validate_on_submit():
            phone_no = phone_number(
                    member_id = member_id,
                    phone_no = contact_form.phone_no.data
                    )
            db.session.add(phone_no)
            db.session.commit()

            flask.flash('Contact added successfully.')
            return flask.redirect(
                    flask.url_for('profiles.personal', member_id = member_id))

        return flask.render_template('profiles/member_profile.html', 
                documents = documents, phone_nos = phone_nos, document_form = doc_form, 
                contact_form = contact_form, tab_variable = tab_variable, member = Member,
                group = Group)


    elif tab_variable == 1:
        fees = registration_fee.query.filter_by(member_id = member_id)\
                .order_by(registration_fee.fee_id.desc()).all()

        form = RegistrationFeeForm()
        if form.validate_on_submit():
            Fee = registration_fee(
                    amount = form.amount.data,
                    member_id = member_id
                    )
            db.session.add(Fee)
            db.session.commit()

            flask.flash(f'Registration Fee  of Ksh. {form.amount.data} Paid Successfully')
            return flask.redirect(
                flask.url_for('profiles.member_profile', member_id = Member.member_id))

        return flask.render_template('profiles/member_profile.html', form = form, 
                tab_variable = tab_variable, member = Member, fees = fees, group = Group)


    elif tab_variable == 2:

        deposits = monthly_deposit.query.filter_by(member_id = member_id)\
                .join(month, month.month_id == monthly_deposit.month_id)\
                .add_columns(
                        monthly_deposit.deposit_id,
                        monthly_deposit.date_created,
                        monthly_deposit.amount,
                        month.month_id,
                        month.description
                        ).order_by(monthly_deposit.deposit_id.asc()).all()

        form = MonthlyDepositForm()

        months = month.query.order_by(month.month_id.desc()).all()
        form.month_id.choices = [((month.month_id), (month.description)) 
                for month in months]

        if form.validate_on_submit():
            Deposit = monthly_deposit(
                    member_id = member_id,
                    amount = form.amount.data,
                    month_id = form.month_id.data)
            db.session.add(Deposit)
            db.session.commit()

            flask.flash(f'Monthly deposit of Ksh. {form.amount.data} was successful.')
            return flask.redirect(
                    flask.url_for('profiles.member_profile', member_id = member_id))

        return flask.render_template('profiles/member_profile.html', deposits = deposits, 
                form = form, tab_variable = tab_variable, member = Member,
                group = Group)

    elif tab_variable == 3:
        loans = loan.query.filter_by(member_id = member_id)\
                .order_by(loan.loan_id.desc()).all()

        form = LoanForm()

        loan_types = loan_type.query.order_by(loan_type.description.desc()).all()
        form.loan_type.choices = [((loan_type.loan_type_id), (loan_type.description)) 
                for loan_type in loan_types]

        if form.validate_on_submit():
            Loan = loan(
                    member_id = member_id,
                    loan_type = form.loan_type.data,
                    amount = form.amount.data
                    )
            db.session.add(Loan)
            db.session.commit()

            flask.flash(f'Loan of Ksh. {form.amount.data} successfully acquired.')
            return flask.redirect(
                    flask.url_for('profiles.member_profile', member_id = member_id))

        return flask.render_template('profiles/member_profile.html', loans = loans, 
            form = form, member = Member, tab_variable = tab_variable, group = Group)

    elif tab_variable == 4:
        employments = employment.query.filter_by(member_id = member_id)\
                .join(employer, employer.employer_id == employment.employer_id)\
                .join(occupation, occupation.occupation_id == employment.occupation_id)\
                .add_columns(
                        employer.employer_id,
                        employer.name,
                        occupation.occupation_id,
                        occupation.description,
                        employment.employment_id,
                        employment.status
                        )
        
        form = EmploymentForm()

        employers = employer.query.order_by(employer.name.desc()).all()
        occupations = occupation.query.order_by(occupation.description.desc()).all()

        form.employer_id.choices = [((employer.employer_id), (employer.name)) 
                for employer in employers]
        
        form.occupation_id.choices = [((occupation.occupation_id), 
            (occupation.description)) for occupation in occupations]

        if form.validate_on_submit():
            Employment = employment(
                    member_id = member_id,
                    employer_id = form.employer_id.data,
                    occupation_id = form.occupation_id.data
                    )
            db.session.add(Employment)
            db.session.commit()

            flask.flash(f'Registration successful.')
            return flask.redirect(
                    flask.url_for('profiles.member_profile', member_id = member_id))

        return flask.render_template('profiles/member_profile.html', form = form,
                member = Member, employments = employments, tab_variable = tab_variable,
                group = Group)

    return flask.render_template('profiles/member_profile.html', 
            tab_variable = tab_variable, member = Member, group = Group)


@profiles.route('/list_of_members')
@login_required
@permission_required(Permission.VIEW)
def list_of_members():
    page = flask.request.args.get('page', 1, type = int)  
    pagination = member.query.order_by(member.member_id.desc())\
            .paginate(page, per_page = flask.current_app.config['FLASKY_POSTS_PER_PAGE'], 
                    error_out = False)

    members = pagination.items
    return flask.render_template('profiles/list_of_members.html', members = members, 
            pagination = pagination)


@profiles.route('/user_profile')
@login_required
@permission_required(Permission.REGISTER)
def user_profile():
    role_id = current_user.role_id
    Role = role.query.filter_by(role_id = role_id).first()
    return flask.render_template('profiles/user_profile.html', Role = Role)


@profiles.route('/list of users')
@login_required
@permission_required(Permission.VIEW)
def list_of_users():
    page = flask.request.args.get('page', 1, type = int)
    pagination = user.query.order_by(user.id.asc())\
            .join(role, role.role_id == user.role_id)\
            .add_columns(
                user.id,
                user.gender,
                user.first_name,
                user.middle_name,
                user.last_name,
                user.email_address,
                role.role_id,
                role.name.label('role')
            ).paginate(page, 
                    per_page = flask.current_app.config['FLASKY_POSTS_PER_PAGE'], 
                    error_out = False)
    users = pagination.items

    return flask.render_template('profiles/list_of_users.html', users = users, 
            pagination = pagination)

@profiles.route("/management")
@login_required
def management():
    teams = {}
    roles = role.query.all()
    for item in roles:
        users = user.query.filter_by(role_id = item.role_id).limit(6)
        teams.update({item : users})

    selected = ["Administrator", "Senior Staff", "Junior Staff", "Security Personnel"]
    return flask.render_template("profiles/management.html", teams = teams, 
            selected = selected)


@profiles.route('/management_category/<int:role_id>')
@login_required
def management_category(role_id):
    category = role.query.filter_by(role_id = role_id).first()
    page = flask.request.args.get('page', 1, type = int)
    pagination = user.query.filter_by(role_id = role_id).order_by(user.first_name.desc())\
            .paginate(page, flask.current_app.config['FLASKY_POSTS_PER_PAGE'], 
                    error_out = False)
    users = pagination.items
    return flask.render_template('profiles/management_category.html', users = users, 
            pagination = pagination, category = category)


@profiles.route('/list_of_groups')
def list_of_groups():
    page = flask.request.args.get('page', 1, type = int)
    pagination = group.query.order_by(group.name.desc()).paginate(page, 
            flask.current_app.config['FLASKY_POSTS_PER_PAGE'], error_out = False)
    groups = pagination.items

    return flask.render_template('profiles/list_of_groups.html', groups = groups, 
            pagination = pagination)


@profiles.route('/group/personal/<int:group_id>')
@login_required
def group_personal(group_id):
    response = flask.make_response(
        flask.redirect(flask.url_for('profiles.group_profile', group_id = group_id)))
    response.set_cookie('tab_var', '0', max_age = 60*60)
    return response


@profiles.route('/group/registration_fees/<int:group_id>')
@login_required
def group_registration_fees(group_id):
    response = flask.make_response(flask.redirect(
        flask.url_for('profiles.group_profile', group_id = group_id)))
    response.set_cookie('tab_var', '1', max_age = 60*60)
    return response


@profiles.route('/group/monthly_deposits/<int:group_id>')
@login_required
def group_monthly_deposits(group_id):
    response = flask.make_response(
        flask.redirect(flask.url_for('profiles.group_profile', group_id = group_id)))
    response.set_cookie('tab_var', '2', max_age = 60*60)
    return response


@profiles.route('/group/loans/<int:group_id>')
@login_required
def group_loans(group_id):
    response = flask.make_response(
        flask.redirect(flask.url_for('profiles.group_profile', group_id = group_id)))
    response.set_cookie('tab_var', '3', max_age = 60*60)
    return response


@profiles.route('/group_profile/<int:group_id>', methods = ['GET', 'POST'])
def group_profile(group_id):
    Group = group.query.filter_by(group_id = group_id).first()

    tab_variable = 0
    if flask.request.cookies.get('tab_var') is not None:
        tab_variable = int(flask.request.cookies.get('tab_var'))

    if tab_variable == 0:
        members = member.query.filter_by(group_id = group_id).all()
        return flask.render_template('profiles/group_profile.html', group = Group,
            tab_variable = tab_variable, members = members)

    elif tab_variable == 1:
        fees = member.query.filter_by(group_id = group_id)\
                .join(registration_fee, registration_fee.member_id == member.member_id)\
                .add_columns(
                        member.member_id,
                        member.first_name,
                        member.middle_name,
                        member.last_name,
                        registration_fee.fee_id,
                        registration_fee.amount,
                        registration_fee.date_created
                    ).order_by(registration_fee.fee_id.desc()).all()
        return flask.render_template('profiles/group_profile.html', group = Group,
            tab_variable = tab_variable, fees = fees)

    elif tab_variable == 2:
        deposits = member.query.filter_by(group_id = group_id)\
            .join(monthly_deposit, monthly_deposit.member_id == member.member_id)\
            .join(month, month.month_id == monthly_deposit.month_id)\
            .add_columns(
                    member.member_id,
                    member.first_name,
                    member.middle_name,
                    member.last_name,
                    member.gender,
                    month.month_id,
                    month.description,
                    monthly_deposit.deposit_id,
                    monthly_deposit.amount,
                    monthly_deposit.date_created
                ).order_by(monthly_deposit.deposit_id.desc())
        return flask.render_template('profiles/group_profile.html', group = Group,
            tab_variable = tab_variable, deposits = deposits)

    elif tab_variable == 3:
        loans = member.query.filter_by(group_id = group_id)\
                .join(loan, loan.member_id == member.member_id)\
                .join(loan_type, loan_type.loan_type_id == loan.loan_type)\
                .add_columns(
                        member.member_id,
                        member.first_name,
                        member.middle_name,
                        member.last_name,
                        loan.loan_id,
                        loan.amount,
                        loan.status,
                        loan.date_created,
                        loan_type.loan_type_id,
                        loan_type.description
                    ).order_by(loan.loan_id.desc()).all()
        return flask.render_template('profiles/group_profile.html', group = Group,
            tab_variable = tab_variable, loans = loans)

    return flask.render_template('profiles/group_profile.html', group = Group, 
        tab_variable = tab_variable)
