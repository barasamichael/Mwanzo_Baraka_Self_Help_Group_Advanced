from flask import Blueprint, current_app
authentication = Blueprint('authentication', __name__)
from . import views, errors

@authentication.app_context_processor
def global_variables():
    return dict(app_name = current_app.config['ORGANISATION_NAME'])
