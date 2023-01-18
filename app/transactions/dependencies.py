import os, flask, time
from sqlalchemy import func
from datetime import datetime, timedelta, date
from .. import create_app, db


from ..models import (member, group, user, loan, loan_type, monthly_deposit, 
        monthly_deposit_overdue, loan_overdue, deposit_overdue_payment, 
        loan_overdue_payment, installment, month, registration_fee)

def generate_month(description = datetime.utcnow().strftime("%B %Y")):
    """
    Converts string representation of month to its numeral representation
        description is string representation of month e.g., "July 2020"
    """
    data = {"January" : 1, "February" : 2, "March" : 3, 
            "April" : 4, "May" : 5, "June" : 6, 
            "July" : 7, "August" : 8, "September" : 9, 
            "October" : 10, "November" : 11, "December" : 12
            }

    return data.get(description.split()[0])


def all_monthly_deposits():
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')

    with app.app_context():
        months = month.query.all()
        deposits_data = []
        for item in months:
            deposits = db.session.query(func.sum(monthly_deposit.amount))\
                .filter_by(month_id = item.month_id).scalar()

            data = {
                'month' : item.description,
                'count' : item.deposits.count(),
                'total' : deposits
            }
            deposits_data.append(data)
    return deposits_data


def monthly_records_summary_generator(year = 2020):

    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    with app.app_context():
        months = month.query.filter(month.description.endswith(str(year))).all()
        month_data = list()
        for item in months: 
            month_start = datetime(year, generate_month(item.description), 1,1,1,1,1)
            try:
                month_stop = datetime(year, generate_month(item.description) + 1,1,1,1,1)
            except:
                month_stop = datetime(year + 1, 1, 1, 1, 1, 1)

            month_installments = db.session.query(
                    func.count(installment.installment_id).label('count'), 
                    func.sum(installment.amount).label('total')).filter(
                installment.date_created.between(month_start, month_stop)).all()

            month_overdues = db.session.query(
                    func.count(loan_overdue.loan_overdue_id).label('count'),
                    func.sum(loan_overdue.amount).label('total')).filter(
                loan_overdue.date_created.between(month_start, month_stop)).all()

            month_overdue_payments = db.session.query(
                    func.count(loan_overdue_payment.amount).label('count'),
                    func.sum(loan_overdue_payment.amount).label('total')).filter(
                loan_overdue_payment.date_created.between(month_start, month_stop)).all()
        
            month_loans = db.session.query(
                    func.count(loan.loan_id).label('count'),
                    func.sum(loan.amount).label('total')).filter(
                loan.date_created.between(month_start, month_stop)).all()

            month_registration_fees = db.session.query(
                    func.count(registration_fee.amount).label('count'),
                    func.sum(registration_fee.amount).label('total')).filter(
                registration_fee.date_created.between(month_start, month_stop)).all()
        
            month_deposits = db.session.query(
                    func.count(monthly_deposit.amount).label('count'),
                    func.sum(monthly_deposit.amount).label('total')).filter(
                monthly_deposit.date_created.between(month_start, month_stop)).all()

            month_deposit_overdue_payments = db.session.query(
                        func.count(deposit_overdue_payment.amount).label('count'),
                        func.sum(deposit_overdue_payment.amount).label('total')).filter(
                    deposit_overdue_payment.date_created.between(month_start, month_stop)
                ).all()

            month_deposit_overdues = db.session.query(
                        func.count(monthly_deposit_overdue.amount).label('count'),
                        func.sum(monthly_deposit_overdue.amount).label('total')).filter(
                    monthly_deposit_overdue.date_created.between(month_start, month_stop)
                ).all()

            data = {
                'description' : item.description,
                'deposits' : month_deposits,
                'installments' : month_installments,
                'loans' : month_loans,
                'loan overdues' : month_overdues,
                'overdue payments' : month_overdue_payments,
                'registration fees' : month_registration_fees,
                'deposit overdues' : month_deposit_overdues,
                'deposit overdue payments' : month_deposit_overdue_payments
                }
            month_data.append(data)
    return month_data

def year_summary_data_generator():
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    with app.app_context():

        year_comparison = list()
        for item in range(flask.current_app.config['FIRST_YEAR'], 
                int(time.strftime("%Y"))):
            year_start = datetime(item, 1, 1, 1, 1, 1)
            year_stop = datetime(item + 1, 1, 1, 1, 1, 1)

            compare_deposits = db.session.query(
                    func.sum(monthly_deposit.amount).label('total')).filter(
                monthly_deposit.date_created.between(year_start, year_stop)).scalar()

            compare_installments = db.session.query(
                    func.sum(installment.amount).label('total')).filter(
                installment.date_created.between(year_start, year_stop)).scalar()

            compare_loans = db.session.query(
                    func.sum(loan.amount).label('total')).filter(
                loan.date_created.between(year_start, year_stop)).scalar()

            compare_registration_fees = db.session.query(
                    func.sum(registration_fee.amount).label('total')).filter(
                registration_fee.date_created.between(year_start, year_stop)).scalar()

            compare_overdue_payments = db.session.query(
                    func.sum(loan_overdue_payment.amount).label('total')).filter(
                loan_overdue_payment.date_created.between(year_start, year_stop)).scalar()

            compare_deposit_overdue_payments = db.session.query(
                    func.sum(deposit_overdue_payment.amount).label('total'))\
                .filter(deposit_overdue_payment.date_created.between(
                    year_start, year_stop)).scalar()

            compare_loan_interests = db.session.query(
                    func.count(loan.loan_id),
                    func.sum(loan_type.rate * loan.amount * loan_type.max_period * 12)
                ).join(loan_type, loan_type.loan_type_id == loan.loan_type).filter(
                        loan.status == 'Paid', 
                        loan.last_updated.between(year_start, year_stop)).all()

            comparison_data = {
                'financial year' : item,
                'monthly deposits' : compare_deposits,
                'installments' : compare_installments,
                'supplied loans' : compare_loans,
                'loan overdue payments' : compare_overdue_payments,
                'registration fees' : compare_registration_fees,
                'fully paid loan interest' : compare_loan_interests[0][1],
                'monthly deposit overdue payments' : compare_deposit_overdue_payments
                }
            year_comparison.append(comparison_data)
    return year_comparison

def update_overdue_monthly_deposits(period = 12):
    """Retrieves all overdue monthly deposit payments for all members for the last {period} months."""
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')

    ### failed implementation of time constraint

    with app.app_context():
        months = month.query.all()
        for member_item in member.query.all():
            for month_item in months:
                if member_item.date_created < datetime.strptime(month_item.description, "%B %Y"):
                    #check whether there is an existing overdue record for member on month_item
                    overdues = monthly_deposit_overdue.query.filter(
                            monthly_deposit_overdue.member_id == member_item.member_id,
                            monthly_deposit_overdue.month_id == month_item.month_id).first()
                    if overdues:
                        continue #a record already exists; no need to continue with process

                    #check whether member in question has made any deposit for the month
                    deposits = db.session.query(func.sum(monthly_deposit.amount))\
                        .filter(
                            monthly_deposit.month_id == month_item.month_id,
                            monthly_deposit.member_id == member_item.member_id).scalar()
                    if not deposits:
                        deposits = 0

                    if (deposits == 0) or (deposits < flask.current_app.config['DEPOSIT_OVERDUE']):
                        overdue = monthly_deposit_overdue(
                                amount = flask.current_app.config['DEPOSIT_OVERDUE'] - deposits,
                                month_id = month_item.month_id,
                                member_id = member_item.member_id)
                        db.session.add(overdue)
                        print(f'Generation of overdue monthly deposit for ID {member_item.member_id} - {month_item.description}')
    db.session.commit()
    return None
