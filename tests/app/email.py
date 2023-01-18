from flask import current_app
from  flask_mail import Message
from . import mail

def send_mail(to, subject,template, **kwargs):
    message = Message(current_app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject, \
            sender = current_app.config['FLASKY_MAIL_SENDER'], \
            recepients = [to])

    message.body = flask.render_template(template + '.txt', **kwargs)
    mail.send(message)
