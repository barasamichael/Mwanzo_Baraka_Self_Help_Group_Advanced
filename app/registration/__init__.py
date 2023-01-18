from flask import Blueprint, current_app
registration = Blueprint('registration' , __name__)
from . import views, errors, dependencies
from ..models import Permission

@registration.app_context_processor
def global_variables():
    return dict(app_name = current_app.config['ORGANISATION_NAME'], 
            Permission = Permission)
