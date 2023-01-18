import os
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))
today = datetime.utcnow()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or \
            'Fighting poverty, ignorance and diseases'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = os.environ.get('MAIL_PORT', '587')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true')\
            .lower() in ['True', 'on', 1]
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    FLASKY_ADMIN_EMAIL = os.environ.get('FLASKY_ADMIN_EMAIL')\
            or 'mwanzobarakauser001@gmail.com'
    FLASKY_MAIL_SUBJECT_PREFIX = os.environ.get('FLASKY_MAIL_SUBJECT_PREFIX')\
            or '[Mwanzo Baraka Self Help Group]'
    FLASKY_MAIL_SENDER = os.environ.get('FLASKY_MAIL_SENDER')\
            or 'Mwanzo Baraka Self Help Group Admin <mwanzobarakaorg@gmail.com>'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ORGANISATION_NAME = os.environ.get('ORGANISATION_NAME') or 'Mwanzo Baraka Self Help Group'
    
    FLASKY_RECORDS_PER_PAGE = os.environ.get('FLASKY_RECORDS_PER_PAGE') or 24
    FLASKY_ITEMS_PER_PAGE = os.environ.get('FLASKY_ITEMS_PER_PAGE') or 12
    DEPOSIT_OVERDUE = os.environ.get('DEPOSIT_OVERDUE') or 1000
    FLASKY_POSTS_PER_PAGE = os.environ.get('FLASKY_POSTS_PER_PAGE') or 24

    GROUP_UPLOAD_PATH = os.path.join(basedir + '/app/static/profiles/groups')
    INDIVIDUAL_UPLOAD_PATH = os.path.join(basedir + '/app/static/profiles/member')
    USER_UPLOAD_PATH = os.path.join(basedir + '/app/static/profiles/user')
    DOCUMENT_UPLOAD_PATH = os.path.join(basedir + '/app/static/documents')
    GALLERY_UPLOAD_PATH = os.path.join(basedir + '/app/static/gallery')
    BRANCH_UPLOAD_PATH = os.path.join(basedir + '/app/static/branches')

    UPLOAD_EXTENSIONS = ['.jpg', '.gif', '.jpeg', '.png']
    FIRST_YEAR = os.environ.get('FIRST_YEAR') or (int(today.strftime("%Y")) - 5)


@staticmethod
def init_app(app):
    pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') \
            or 'sqlite:///' + os.path.join(basedir, 'data-dev-sqlite')
    

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite://'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') \
            or 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config = {
        'development' : DevelopmentConfig,
        'testing' : TestingConfig,
        'production' : ProductionConfig,
        'default' : DevelopmentConfig
        }





