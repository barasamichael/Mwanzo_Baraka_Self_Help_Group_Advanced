import flask, os
from .. import db, create_app
from ..models import user, member, group

def change_user_status(user_id):
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')

    with app.app_context():
        User = user.query.filter_by(id = user_id).first_or_404()
        User.active = not User.active

        db.session.add(User)
        db.session.commit()

    return User

def change_member_status(member_id, deactivate_all = False):
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')

    with app.app_context():
        Member = member.query.filter_by(member_id = member_id).first_or_404()

        if Member.status == 'activated':
            Member.status = 'deactivated'
        else:
            Member.status = 'activated'

        if deactivate_all:
            Member.status = 'deactivated'

        db.session.add(Member)
        db.session.commit()

    return Member

def change_group_status(group_id):
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')

    with app.app_context():
        Group = group.query.filter_by(group_id = group_id).first_or_404()

        #deactivate group
        Group.active = not Group.active

        #deactivate all members of the group
        for item in member.query.filter_by(group_id = group_id).all():
            Group = group.query.filter_by(group_id = group_id).first_or_404()
            if not Group.active:
                change_member_status(item.member_id, True)
            else:
                change_member_status(item.member_id)

        db.session.add(Group)
        db.session.commit()

    return Group
