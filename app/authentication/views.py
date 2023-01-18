import flask
from flask_login import login_user, logout_user, login_required
from . import authentication
from .. import db
from ..models import user
from .forms import LoginUserForm

@authentication.route('/logout')
@login_required
def logout():
    """
    Logs out current user and informs the user.
    """
    logout_user()
    flask.flash("You've been logged out.")
    return flask.redirect(flask.url_for('authentication.login'))


@authentication.route('/login', methods = ['GET', 'POST'])
def login():
    """
    Accepts and validates the user credentials
    Redirects authenticated user to page last redirected from or user profile page
    Accepts no arguments
    """
    form = LoginUserForm()

    if form.validate_on_submit():
        User = user.query.filter_by(email_address = form.email_address.data).first()
        
        if User is not None and User.verify_password(form.password.data):
            login_user(User, form.remember_me.data)
            next = flask.request.args.get('next')

            if next is None or not next.startswith('/'):
                next = flask.url_for('profiles.user_profile')

            return flask.redirect(next)
        flask.flash('Invalid email address or password')
    return flask.render_template('authentication/login.html', form = form)
