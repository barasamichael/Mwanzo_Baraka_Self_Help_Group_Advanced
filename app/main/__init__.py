from flask import Blueprint, current_app
main = Blueprint('main', __name__)
from . import views, errors

@main.app_context_processor
def global_variables():
    return dict(app_name = current_app.config['ORGANISATION_NAME'])
