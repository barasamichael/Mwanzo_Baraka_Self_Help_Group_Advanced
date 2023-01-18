import flask, time, random, os
from sqlalchemy import func
from datetime import datetime
from . import transactions
from .. import db, create_app

from ..decorators import permission_required
from ..models import (member, group, user, loan, loan_type, monthly_deposit, 
        monthly_deposit_overdue, loan_overdue, deposit_overdue_payment, 
        loan_overdue_payment, installment, month, registration_fee, Permission)

from .forms import (InstallmentForm, OverduePaymentForm, UpdateOverdueMonthlyDepositsFiltersForm)
from .graphs import (YearsComparisonGraph, MonthlyDepositsGraph)
from .dependencies import (monthly_records_summary_generator, year_summary_data_generator,
        generate_month, all_monthly_deposits, update_overdue_monthly_deposits)
from flask_login import login_required, current_user

@transactions.route('/graphs')
@login_required
@permission_required(Permission.VISIT)
def graphs():
    deposits_chart = DepositsChart()
    deposits_chart.data.label = "Comparison on Monthly Deposits"

    for year in range(flask.current_app.config['FIRST_YEAR'], int(time.strftime("%Y"))):
        year_start = datetime(year, 1, 1, 1, 1, 1)
        year_stop = datetime(year + 1, 1, 1, 1, 1, 1)

        compare_deposits = db.session.query(
                func.sum(monthly_deposit.amount).label('total')).filter(
            monthly_deposit.date_created.between(year_start, year_stop)).scalar()

        if compare_deposits:
            deposits_chart.data.data.append(compare_deposits)

    deposits_json = deposits_chart.get()
    return flask.render_template('transactions/graphs.html', deposits_json =deposits_json)


@transactions.route('/year_summary/<int:year>')
@login_required
@permission_required(Permission.VISIT)
def year_summary(year):
    start = datetime(year, 1, 1, 1, 1, 1, 1)
    stop = datetime(year + 1, 1, 1, 1, 1, 1, 1)

    loans_supplied = db.session.query(
            func.count(loan.loan_id).label('count'),
            func.sum(loan.amount).label('total'))\
                .filter(loan.date_created.between(start, stop)).all()

    paid_loans = db.session.query(
            func.count(loan.loan_id).label('count'),
            func.sum(loan.amount).label('total')).filter(
                loan.last_updated.between(start, stop), loan.status == 'Paid').all()

    pending_loans = db.session.query(
            func.count(loan.loan_id).label('count'),
            func.sum(loan.amount).label('total')).filter(
                loan.date_created < stop, loan.status == 'pending').all()

    overdue_loans = db.session.query(
            func.count(loan_overdue.month).label('count'),
            func.sum(loan_overdue.amount).label('total')).filter(
            loan_overdue.date_created < stop, loan_overdue.status == 'pending').all()

    installments = db.session.query(
            func.sum(installment.amount).label('total'),
            func.count(installment.installment_id).label('count'))\
                    .filter(installment.date_created.between(start, stop)).all()

    total_members = db.session.query(func.count(member.member_id)).filter(
            member.date_created < stop).scalar()
    
    new_members = db.session.query(func.count(member.member_id)).filter(
            member.date_created.between(start, stop)).scalar()

    total_employees = db.session.query(func.count(user.id)).filter(
            user.date_created < stop).scalar()

    new_employees = db.session.query(func.count(user.id)).filter(
            user.date_created.between(start, stop)).scalar()


    year_data = {
            "loans supplied" : loans_supplied,
            "paid loans" : paid_loans,
            "pending loans" : pending_loans,
            "overdue loans" : overdue_loans,
            "installments" : installments,
            "total members" : total_members,
            "new members" : new_members,
            "total employees" : total_employees,
            "new employees" : new_employees
            }

    aggregate_deposits = db.session.query(
            func.count(monthly_deposit.amount).label('count'), 
            func.sum(monthly_deposit.amount).label('total')).filter(
        monthly_deposit.date_created.between(start, stop)).all()

    aggregate_installments = db.session.query(
            func.count(installment.amount).label('count'),
            func.sum(installment.amount).label('total')).filter(
        installment.date_created.between(start, stop)).all()

    aggregate_loans = db.session.query(
            func.count(loan.amount).label('count'),
            func.sum(loan.amount).label('total')).filter(
        loan.date_created.between(start, stop)).all()

    aggregate_overdue_payments = db.session.query(
            func.count(loan_overdue_payment.amount).label('count'),
            func.sum(loan_overdue_payment.amount).label('total')).filter(
        loan_overdue_payment.date_created.between(start, stop)).all()

    aggregate_registration_fees = db.session.query(
            func.count(registration_fee.amount).label('count'),
            func.sum(registration_fee.amount).label('total')).filter(
        registration_fee.date_created.between(start, stop)).all()

    aggregate_deposit_overdue_payments = db.session.query(
            func.count(deposit_overdue_payment.amount).label('count'),
            func.sum(deposit_overdue_payment.amount).label('total')).filter(
        deposit_overdue_payment.date_created.between(start, stop)).all()
        
    aggregate_loan_interests = db.session.query(
        func.count(loan.amount).label('count'),
        func.sum(
            loan_type.rate * loan.amount * loan_type.max_period * 12).label('total'))\
                    .join(loan_type, loan_type.loan_type_id == loan.loan_type)\
        .filter(loan.status == 'Paid', loan.last_updated.between(start, stop)).all()

    aggregate_data = {
            'monthly deposits' : aggregate_deposits,
            'installments' : aggregate_installments,
            'supplied loans' : aggregate_loans,
            'loan overdue payments' : aggregate_overdue_payments,
            'registration fees' : aggregate_registration_fees,
            'fully paid loan interest' : aggregate_loan_interests,
            'monthly deposit overdue payments' : aggregate_deposit_overdue_payments
            }

    gross_profit_data = (aggregate_deposit_overdue_payments[0][1], 
            aggregate_overdue_payments[0][1], aggregate_registration_fees[0][1], 
            aggregate_loan_interests[0][1])

    gross_profit = 0
    for item in gross_profit_data:
        if item:
            gross_profit += item

    dividends = 60/100 * gross_profit
    company_profit = 40/100 * gross_profit

    credit = 0
    if aggregate_loans[0][1]:
        credit = aggregate_loans[0][1]

    debit = gross_profit
    if aggregate_deposits[0][1]:
        debit += aggregate_deposits[0][1]

    profits = {
            'dividends' :dividends,
            'company profit' : company_profit,
            'gross profit' : gross_profit,
            'credit' : credit,
            'debit' : debit
            }
    year_comparison = year_summary_data_generator()
    month_data = monthly_records_summary_generator() 
    
    years_comparison_graph = YearsComparisonGraph()
    years_comparison_JSON = years_comparison_graph.get()

    return flask.render_template('transactions/year_summary.html', year = year, 
        month_data = month_data, aggregate_data = aggregate_data, year_data = year_data,
        profits = profits, year_comparison = year_comparison, 
        years_comparison_JSON = years_comparison_JSON)


@transactions.route('/summary')
@login_required
@permission_required(Permission.VISIT)
def summary():
    deposits_data = all_monthly_deposits()
    all_monthly_deposits_graph = MonthlyDepositsGraph()
    all_monthly_deposits_JSON = all_monthly_deposits_graph.get()

    year_comparison = year_summary_data_generator()
    month_data = monthly_records_summary_generator() 
    
    years_comparison_graph = YearsComparisonGraph()
    years_comparison_JSON = years_comparison_graph.get()

    years = [item for item in range(flask.current_app.config['FIRST_YEAR'], 
        int(datetime.utcnow().strftime("%Y")))]


    return flask.render_template('transactions/summary.html',deposits_data=deposits_data,
        all_monthly_deposits_JSON = all_monthly_deposits_JSON, years = years,
        years_comparison_JSON = years_comparison_JSON, year_comparison = year_comparison)


@transactions.route('/pay_loan_overdue/<int:loan_overdue_id>', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MEMBER)
def pay_loan_overdue(loan_overdue_id):
    form = OverduePaymentForm()

    if form.validate_on_submit():
        Loan_Overdue = loan_overdue.query.get_or_404(loan_overdue_id)
        
        paid = db.session.query(func.sum(loan_overdue_payment.amount))\
            .filter_by(loan_overdue_id = loan_overdue_id).scalar()
        
        if not paid:
            paid = 0

        if Loan_Overdue and form.amount.data <= (Loan_Overdue.amount - paid):
            payment = loan_overdue_payment(
                    loan_overdue_id = loan_overdue_id,
                    amount = form.amount.data
                )
            db.session.add(payment)

            if (Loan_Overdue.amount - (paid + form.amount.data)) == 0:
                Loan_Overdue.status = 'Paid'
                db.session.add(Loan_Overdue)

            db.session.commit()

            flask.flash(f"Payment of Ksh. {form.amount.data} successful.")
            return flask.redirect(flask.url_for('transactions.loan_profile', 
                loan_id = Loan_Overdue.loan_id))
        
        flask.flash('You made an over payment. Please pay the required amount.')
        return flask.redirect(flask.url_for('transactions.loan_profile',
                loan_id = Loan_Overdue.loan_id))
    return flask.render_template('transactions/pay_loan_overdue.html', form = form)


@transactions.route('/pay_overdue_monthly_deposit/<int:overdue_id>', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def pay_overdue_monthly_deposit(overdue_id):
    form = OverduePaymentForm()

    if form.validate_on_submit():
        Overdue_Deposit = monthly_deposit_overdue.query.\
                filter_by(monthly_deposit_overdue_id = overdue_id).first()
        paid = db.session.query(func.sum(deposit_overdue_payment.amount)).filter_by(
                monthly_deposit_overdue_id = overdue_id).scalar()

        if not paid:
            paid = 0

        if Overdue_Deposit and form.amount.data <= (1000 - paid):
            Deposit_Overdue_Payment = deposit_overdue_payment(
                amount = form.amount.data,
                monthly_deposit_overdue_id = overdue_id
            )
            db.session.add(Deposit_Overdue_Payment)

            if 1000 - (paid + form.amount.data) == 0:
                Overdue_Deposit.status = 'paid'
                db.session.add(Overdue_Deposit)
            
            db.session.commit()

            credit = 1000 - (paid + form.amount.data)
            flask.flash(f'Loan Overdue Payment Successful. Your have a credit of Ksh. {credit}')
            return flask.redirect(flask.url_for('transactions.monthly_deposit_overdue_profile', 
                overdue_id = overdue_id))
        
        flask.flash('The amount entered superseeds the required amount. Please revise amount.')
        return flask.redirect(
                flask.url_for('transactions.pay_overdue_monthly_deposit', overdue_id = overdue_id))
        
    return flask.render_template('transactions/pay_overdue_monthly_deposit.html', form = form)

@transactions.route('/overdue_monthly_deposit_payments')
@login_required
@permission_required(Permission.REGISTER)
def overdue_monthly_deposit_payments():
    page = flask.request.args.get('page', 1, type = int)
    pagination = deposit_overdue_payment.query.join(monthly_deposit_overdue, 
            monthly_deposit_overdue.monthly_deposit_overdue_id == 
            deposit_overdue_payment.monthly_deposit_overdue_id)\
            .join(member, member.member_id == monthly_deposit_overdue.member_id)\
            .join(month, month.month_id == monthly_deposit_overdue.month_id)\
            .add_columns(
                    member.member_id,
                    member.first_name,
                    member.middle_name,
                    member.last_name,
                    monthly_deposit_overdue.monthly_deposit_overdue_id,
                    deposit_overdue_payment.deposit_overdue_payment_id.label('payment_id'),
                    deposit_overdue_payment.date_created,
                    deposit_overdue_payment.amount,
                    month.month_id,
                    month.description
            ).order_by(deposit_overdue_payment.deposit_overdue_payment_id.desc()).paginate(page, 
                    flask.current_app.config['FLASKY_POSTS_PER_PAGE'], error_out = False)
    payments = pagination.items

    return flask.render_template('transactions/overdue_monthly_deposit_payments.html', 
            payments = payments, pagination = pagination)

@transactions.route('/monthly_deposit_overdue_profile/<int:overdue_id>')
@login_required
@permission_required(Permission.REGISTER)
def monthly_deposit_overdue_profile(overdue_id):
    overdue = monthly_deposit_overdue.query.filter_by(monthly_deposit_overdue_id = overdue_id)\
            .join(member, member.member_id == monthly_deposit_overdue.member_id)\
            .join(month, month.month_id == monthly_deposit_overdue.month_id)\
            .add_columns(
                    month.month_id,
                    month.description,
                    member.member_id,
                    member.first_name,
                    member.middle_name,
                    member.last_name,
                    monthly_deposit_overdue.monthly_deposit_overdue_id,
                    monthly_deposit_overdue.date_created,
                    monthly_deposit_overdue.last_updated,
                    monthly_deposit_overdue.amount,
                    monthly_deposit_overdue.status
                ).first()

    #extract amount already paid
    paid = db.session.query(func.sum(deposit_overdue_payment.amount))\
            .filter_by(monthly_deposit_overdue_id = overdue_id).scalar()

    if not paid:
        paid = 0 #if no payments made then paid is zero

    #extract all payment records for this overdue record
    page = flask.request.args.get('page', 1, type = int)
    pagination = deposit_overdue_payment.query.filter_by(monthly_deposit_overdue_id = overdue_id)\
        .order_by(deposit_overdue_payment.deposit_overdue_payment_id.desc()).paginate(page, 
            flask.current_app.config['FLASKY_POSTS_PER_PAGE'], error_out = False)
    payments = pagination.items

    return flask.render_template('transactions/monthly_deposit_overdue_profile.html', 
            pagination = pagination, payments = payments, overdue = overdue, paid = paid)


@transactions.route('/overdue_monthly_deposits')
@login_required
@permission_required(Permission.MEMBER)
def overdue_monthly_deposits():
    page = flask.request.args.get('page', 1, type = int)

    pagination = monthly_deposit_overdue.query.join(month, 
            month.month_id == monthly_deposit_overdue.month_id)\
        .join(member, member.member_id == monthly_deposit_overdue.member_id)\
        .add_columns(
                monthly_deposit_overdue.monthly_deposit_overdue_id.label('overdue_id'),
                monthly_deposit_overdue.amount,
                monthly_deposit_overdue.date_created,
                monthly_deposit_overdue.status,
                month.month_id,
                month.description,
                member.member_id,
                member.first_name,
                member.middle_name,
                member.last_name
                ).order_by(monthly_deposit_overdue.monthly_deposit_overdue_id.desc())\
        .paginate(page, per_page = flask.current_app.config['FLASKY_POSTS_PER_PAGE'],
                error_out = False)

    charges = pagination.items
    return flask.render_template('transactions/overdue_monthly_deposits.html', 
            pagination = pagination, charges = charges)


@transactions.route('/overdue_loans')
@login_required
@permission_required(Permission.MEMBER)
def overdue_loans():
    page = flask.request.args.get('page', 1, type = int)
    
    pagination = loan_overdue. query.join(loan, loan.loan_id == loan_overdue.loan_id)\
            .join(member, member.member_id == loan.member_id)\
            .add_columns(
                    loan.loan_id,
                    loan_overdue.loan_overdue_id,
                    loan_overdue.date_created,
                    loan_overdue.amount,
                    loan_overdue.month,
                    loan_overdue.status,
                    member.member_id,
                    member.first_name,
                    member.middle_name,
                    member.last_name
                    ).order_by(loan_overdue.loan_overdue_id.desc()).paginate(page,
                            per_page = flask.current_app.config['FLASKY_POSTS_PER_PAGE'],
                            error_out = False)
    
    charges = pagination.items
    return flask.render_template('transactions/overdue_loans.html', charges = charges, 
            pagination = pagination)


@transactions.route('/loan_profile/<int:loan_id>', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MEMBER)
def loan_profile(loan_id):
    Loan = loan.query.filter_by(loan_id = loan_id)\
            .join(loan_type, loan_type.loan_type_id == loan.loan_type)\
            .join(member, member.member_id == loan.member_id)\
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
                    loan_type.description,
                    loan_type.multiplier,
                    loan_type.max_period,
                    loan_type.overdue_penalty,
                    loan_type.rate
                ).first_or_404()

    total_installments = db.session.query(func.sum(installment.amount))\
            .filter_by(loan_id = loan_id).scalar()
    
    overdue_charges = db.session.query(func.sum(loan_overdue.amount))\
            .filter_by(loan_id = loan_id).scalar()

    overdue_payments = db.session.query(func.sum(loan_overdue_payment.amount))\
        .join(loan_overdue, 
            loan_overdue.loan_overdue_id == loan_overdue_payment.loan_overdue_id)\
        .join(loan, loan.loan_id == loan_overdue.loan_id)\
        .filter_by(loan_id = loan_id).scalar()
    
    if not overdue_payments:
        overdue_payments = 0
    
    if not total_installments:
        total_installments = 0
    
    if not overdue_charges:
        overdue_charges = 0
    
    installments = installment.query.filter_by(loan_id = loan_id).all()
    interest = Loan.amount * (Loan.max_period * 12) * (Loan.rate / 100)

    form = InstallmentForm()
    if form.validate_on_submit():
        if form.amount.data <= ((Loan.amount + interest) - total_installments):
            Installment = installment(
                    amount = form.amount.data,
                    loan_id = loan_id
                    )
            db.session.add(Installment)

            if ((Loan.amount + interest) - (total_installments + form.amount.data)) == 0:
                loan_1 = loan.query.get_or_404(loan_id)
                loan_1.status = "Paid"
                db.session.add(loan_1)
            
            db.session.commit()

            flask.flash(f"Installment of Ksh. {form.amount.data} submitted successfully.")
            return flask.redirect(
                    flask.url_for('transactions.loan_profile', loan_id = loan_id))

        flask.flash("You made an over payment. Please enter the required amount.")
    
    overdues = loan_overdue.query.filter_by(loan_id = loan_id)\
            .order_by(loan_overdue.loan_overdue_id.desc()).all()

    payments = loan_overdue_payment.query.join(loan_overdue, 
            loan_overdue.loan_overdue_id == loan_overdue_payment.loan_overdue_id)\
                    .add_columns(
                            loan_overdue.loan_overdue_id,
                            loan_overdue.loan_id,
                            loan_overdue.month,
                            loan_overdue_payment.date_created,
                            loan_overdue_payment.loan_overdue_payment_id,
                            loan_overdue_payment.amount
                        ).filter_by(loan_id = loan_id).all()

    return flask.render_template('transactions/loan_profile.html', loan = Loan, 
            installments = installments, total_installments = total_installments, 
            overdue_charges = overdue_charges, overdue_payments = overdue_payments,
            payments = payments, overdues = overdues, form = form)
    

@transactions.route('/update_overdue_monthly_deposits', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def update_overdue_monthly_deposit():
    form = UpdateOverdueMonthlyDepositsFiltersForm()
    
    if form.validate_on_submit():
        update_overdue_monthly_deposits(form.period.data)
        return flask.redirect(flask.url_for('transactions.overdue_monthly_deposits'))

    form.period.data = 12 #by default, operation spans a period of the past 12 months
    return flask.render_template('transactions/update_overdue_monthly_deposits.html', form = form)
