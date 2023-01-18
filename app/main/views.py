import flask
from flask_login import login_required
from . import main
from .. import db

from ..decorators import permission_required
from ..models import (member, employment, occupation, loan_type, review, branch, event, 
        event_image, Permission)


@main.route('/')
@main.route('/home')
@main.route('/homepage')
def homepage():
    loans = loan_type.query.order_by(loan_type.description.desc()).all()
    
    reviews = review.query.join(member, member.member_id == review.member_id)\
            .join(employment, employment.member_id == member.member_id)\
            .join(occupation, occupation.occupation_id == employment.occupation_id)\
            .add_columns(
                    member.first_name,
                    member.middle_name,
                    member.last_name,
                    member.associated_image,
                    review.description,
                    occupation.description.label('occupation')
                    ).limit(3)
    return flask.render_template('main/homepage.html', loans = loans, reviews = reviews)


@main.route('/all_reviews')
def all_reviews():
    page = flask.request.args.get('page', 1, type = int)
    pagination = review.query.join(member, member.member_id == review.member_id)\
            .join(employment, employment.member_id == member.member_id)\
            .join(occupation, occupation.occupation_id == employment.occupation_id)\
            .add_columns(
                    member.first_name,
                    member.middle_name,
                    member.last_name,
                    member.associated_image,
                    review.description,
                    occupation.description.label('occupation')
            ).paginate(page, 
                per_page = flask.current_app.config['FLASKY_POSTS_PER_PAGE'], 
                error_out = False)
    reviews = pagination.items

    return flask.render_template('main/all_reviews.html', pagination = pagination, 
            reviews = reviews)


@main.route('/contact_us')
def contact_us():
    return flask.render_template('main/contact_us.html')

@main.route('/branches')
def branches():
    branches = branch.query.all()
    return flask.render_template('main/branches.html', branches = branches)


@main.route('/event_profile/<int:event_id>')
@login_required
@permission_required(Permission.VISIT)
def event_profile(event_id):
    Event = event.query.filter_by(event_id = event_id).first()

    page = flask.request.args.get('page', 1, type = int)
    pagination = event_image.query.filter_by(event_id = event_id)\
        .paginate(page, per_page = flask.current_app.config['FLASKY_POSTS_PER_PAGE'],
                    error_out = False)
    images = pagination.items

    return flask.render_template('main/event_profile.html', event = Event, 
            images = images, pagination = pagination)


@main.route('/list_of_events')
@login_required
@permission_required(Permission.VISIT)
def list_of_events():
    page = flask.request.args.get('page', 1, type = int)
    pagination = event.query.order_by(event.description.asc())\
            .paginate(page, per_page = flask.current_app.config['FLASKY_POSTS_PER_PAGE'], 
                    error_out = False)
    events = pagination.items
    
    return flask.render_template('main/list_of_events.html', events = events, 
            pagination = pagination)


@main.route('/gallery')
@login_required
@permission_required(Permission.VISIT)
def gallery():
    events = [{item:(event_image.query.filter_by(event_id = item.event_id).limit(6))} 
            for item in event.query.all()]
    return flask.render_template('main/gallery.html', events = events)


@main.route('/about_us')
def about_us():
    return flask.render_template('main/about_us.html')
