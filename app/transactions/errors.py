from flask import render_template
from . import transactions


@transactions.app_errorhandler(403)
def forbidden(e):
    return render_template('transactions/403.html'), 403


@transactions.app_errorhandler(404)
def page_not_found(e):
    return render_template('transactions/404.html'), 404


@transactions.app_errorhandler(500)
def internal_server_error(e):
    return render_template('transactions/500.html'), 500
