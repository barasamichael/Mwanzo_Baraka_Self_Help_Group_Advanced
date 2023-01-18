from flask import Blueprint, current_app
transactions = Blueprint('transactions' , __name__)
from . import views, errors, dependencies, graphs

@transactions.app_context_processor
def global_variables():
    return dict(app_name = current_app.config['ORGANISATION_NAME'])
