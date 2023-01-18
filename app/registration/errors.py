from flask import render_template
from . import registration


@registration.app_errorhandler(403)
def forbidden(e):
    return render_template('registration/403.html'), 403


@registration.app_errorhandler(404)
def page_not_found(e):
    return render_template('registration/404.html'), 404


@registration.app_errorhandler(500)
def internal_server_error(e):
    return render_template('registration/500.html'), 500
