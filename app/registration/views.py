import flask, iso3166, os, imghdr
from . import registration, dependencies
from .. import db

from ..decorators import permission_required
from ..models import member, group, user, branch, event, event_image, Permission
from ..email import send_mail

from .forms import (RegisterMemberForm, RegisterGroupForm, RegisterUserForm, 
        UpdateUserProfileForm, UpdateMemberProfileForm, RegisterBranchForm, 
        RegisterEventForm, UpdateGroupProfileForm, ImageForm)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)

    if not format:
        return None

    return '.' + (format if format == 'jpeg' else 'jpg')


@registration.route('/upload_branch_image/<int:branch_id>', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def upload_branch_image(branch_id):
    Branch = branch.query.filter_by(branch_id = branch_id).first()
    
    form = ImageForm()
    
    if form.validate_on_submit():
        uploaded_file = form.file.data
        filename = secure_filename(uploaded_file.filename)

        if filename != '':
            file_ext = os.path.splitext(filename)[1]

            if file_ext not in flask.current_app.config['UPLOAD_EXTENSIONS']\
                    or file_ext != validate_image(uploaded_file.stream):
                        return 'Invalid Image', 400
        
        uploaded_file.save(
            os.path.join(flask.current_app.config['BRANCH_UPLOAD_PATH'], filename))

        Branch.associated_image = filename
        db.session.add(Branch)
        db.session.commit()
        return flask.redirect(flask.url_for('main.branches'))

    return flask.render_template('registration/upload_branch_image.html', form =  form, 
            branch = Branch)


@registration.route('/register_branch', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def register_branch():
    form = RegisterBranchForm()

    if form.validate_on_submit():
        Branch = branch(
                town = form.town.data,
                email_address = form.email_address.data,
                location_address = form.location_address.data,
                phone_no = form.phone_no.data
                )
        db.session.add(Branch)
        db.session.commit()

        flask.flash(f'{form.town.data} Branch registered successfully.')
        return flask.redirect(flask.url_for('profiles.user_profile'))

    return flask.render_template('registration/register_branch.html', form = form)


@registration.route('/upload_event_images/<int:event_id>', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def upload_event_images(event_id):
    Event = event.query.filter_by(event_id = event_id).first()
    
    folder = Event.description
    folder = os.path.join(flask.current_app.config['GALLERY_UPLOAD_PATH'], folder.strip())

    page = flask.request.args.get('page', 1, type = int)
    pagination = event_image.query.filter_by(event_id = event_id)\
            .paginate(page, per_page = flask.current_app.config['FLASKY_POSTS_PER_PAGE'],
                    error_out = False)
    images = pagination.items

    #upload image to database
    if flask.request.method == 'POST':
        uploaded_file = flask.request.files['file']
        filename = secure_filename(uploaded_file.filename)

        if filename != '':
            extension = os.path.splitext(filename)[1]
            if extension not in flask.current_app.config['UPLOAD_EXTENSIONS']\
                    and extension != validate_image(uploaded_file.stream):
                        return 'Invalid Image', 400
            uploaded_file.save(os.path.join(folder, filename))

        #save file in database
        Image = event_image(
                event_id = event_id,
                description = filename)
        db.session.add(Image)
        db.session.commit()

    return flask.render_template('registration/upload_event_images.html', images = images,
        pagination = pagination, event = Event)


@registration.route('/register_event', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def register_event():
    form = RegisterEventForm()
    if form.validate_on_submit():
        Event = event(description = form.description.data)
        
        db.session.add(Event)
        db.session.commit()

        #create images upload folder
        folder = form.description.data
        try:
            os.mkdir(
                os.path.join(flask.current_app.config['GALLERY_UPLOAD_PATH'], 
                    folder.strip()))
        except:
            pass
        
        flask.flash(f"Event {form.description.data} registered successfully.")
        return flask.redirect(flask.url_for('profiles.user_profile'))

    return flask.render_template('registration/register_event.html', form = form)


@registration.route('/update_member_profile/<int:member_id>', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MEMBER)
def update_member_profile(member_id):
    Member = member.query.filter_by(member_id = member_id).first_or_404()

    form = UpdateMemberProfileForm()

    countries_list = [((country.name), (country.name)) for country in iso3166.countries]
    form.nationality.choices = countries_list

    if form.validate_on_submit():
        Member.id_no = form.id_no.data
        Member.first_name = form.first_name.data
        Member.middle_name = form.middle_name.data
        Member.last_name = form.last_name.data
        Member.gender = form.gender.data
        Member.location_address = form.location_address.data
        Member.nationality = form.nationality.data
        Member.date_of_birth = form.date_of_birth.data

        db.session.add(Member)
        db.session.commit()
        flask.flash('Profile update successful.')

        return flask.redirect(flask.url_for('profiles.member_profile', 
            member_id = Member.member_id))
    form.first_name.data = Member.first_name
    form.middle_name.data = Member.middle_name
    form.last_name.data = Member.last_name
    form.gender.data = Member.gender
    form.id_no.data = Member.id_no
    form.nationality.data = Member.nationality
    form.location_address.data = Member.location_address
    form.date_of_birth.data = Member.date_of_birth
    return flask.render_template('registration/update_member_profile.html', 
            member = Member, form = form)


@registration.route('/update_member_profile_image/<int:member_id>', 
        methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MEMBER)
def update_member_profile_image(member_id):
    Member = member.query.filter_by(member_id = member_id).first_or_404()
    
    form = ImageForm()
    if form.validate_on_submit():
        uploaded_file = form.file.data
        filename = secure_filename(uploaded_file.filename)

        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            
            if file_ext not in flask.current_app.config['UPLOAD_EXTENSIONS']\
                    or file_ext != validate_image(uploaded_file.stream):
                        return 'Invalid Image', 400

            uploaded_file.save(os.path.join(
                flask.current_app.config['INDIVIDUAL_UPLOAD_PATH'], filename))

        Member.associated_image = filename
        db.session.add(Member)
        db.session.commit()

        flask.flash('Profile image updated successfully.')
        return flask.redirect(flask.url_for('profiles.member_profile', 
            member_id = Member.member_id))
    
    return flask.render_template('registration/update_member_profile_image.html', 
            member = Member, form = form)


@registration.route('/update_user_profile_image', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def update_user_profile_image():
    form = ImageForm()

    if form.validate_on_submit():
        uploaded_file = form.file.data
        filename = secure_filename(uploaded_file.filename)

        if filename != '':
            file_ext = os.path.splitext(filename)[1]

            if file_ext not in flask.current_app.config['UPLOAD_EXTENSIONS']\
                    or file_ext != validate_image(uploaded_file.stream):
                        return 'Invalid Image', 400

            uploaded_file.save(os.path.join(
                flask.current_app.config['USER_UPLOAD_PATH'], filename))

        current_user.associated_image = filename
        db.session.commit()
        flask.flash('Profile image updated sucessfully')

        return flask.redirect(flask.url_for('profiles.user_profile'))

    return flask.render_template('registration/update_user_profile_image.html', 
            form = form)


@registration.route('update_user_profile', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def update_user_profile():
    form = UpdateUserProfileForm()

    countries_list = [((country.name), (country.name)) for country in iso3166.countries]
    form.nationality.choices = countries_list

    if form.validate_on_submit():
        current_user.id_no = form.id_no.data
        current_user.first_name = form.first_name.data
        current_user.middle_name = form.middle_name.data
        current_user.last_name = form.last_name.data
        current_user.gender = form.gender.data
        current_user.location_address = form.location_address.data
        current_user.nationality = form.nationality.data
        current_user.date_of_birth = form.date_of_birth.data

        db.session.add(current_user)
        db.session.commit()
        flask.flash('Profile updated successfully.')

        return flask.redirect(flask.url_for('profiles.user_profile'))

    form.first_name.data = current_user.first_name
    form.middle_name.data = current_user.middle_name
    form.last_name.data = current_user.last_name
    form.id_no.data = current_user.id_no
    form.gender.data = current_user.gender
    form.nationality.data = current_user.nationality
    form.location_address.data = current_user.location_address
    form.date_of_birth.data = current_user.date_of_birth

    return flask.render_template('registration/update_user_profile.html', form = form)


@registration.route('register_user', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE)
def register_user():
    form = RegisterUserForm()

    countries_list = [((country.name), (country.name)) for country in iso3166.countries]
    form.nationality.choices = countries_list
    
    if form.validate_on_submit():
        User = user(
            id_no = form.id_no.data,
            first_name = form.first_name.data,
            middle_name = form.middle_name.data,
            last_name = form.last_name.data,
            gender = form.gender.data,
            email_address = form.email_address.data,
            location_address = form.location_address.data,
            nationality = form.nationality.data,
            date_of_birth = form.date_of_birth.data,
            password = form.password.data
        ) 
        db.session.add(User)
        db.session.commit()

        #confirmation email
        token = User.generate_confirmation_token()
        #send_mail(User.email_address, 'Confirm Your Account','registration/email/confirm',
        #    app_name = flask.current_app.config['ORGANISATION_NAME'], token = token, 
        #    User = User)
        flask.flash("A confirmation email has been sent to you by email.")

        return flask.redirect(flask.url_for('authentication.login'))
    
    return flask.render_template('registration/register_user.html', form = form)


@registration.route('/upload_group_image/<int:group_id>', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.REGISTER)
def upload_group_image(group_id):
    Group = group.query.filter_by(group_id = group_id).first()
    form = ImageForm()
    
    if form.validate_on_submit():
        uploaded_file = form.file.data
        filename = secure_filename(uploaded_file.filename)

        if filename != '':
            file_ext = os.path.splitext(filename)[1]

            if file_ext not in flask.current_app.config['UPLOAD_EXTENSIONS']\
                    or file_ext != validate_image(uploaded_file.stream):
                        return 'Invalid Image', 400
        
        uploaded_file.save(
            os.path.join(flask.current_app.config['GROUP_UPLOAD_PATH'], filename))

        Group.associated_image = filename
        db.session.add(Group)
        db.session.commit()
        return flask.redirect(
                flask.url_for('profiles.group_profile', group_id = Group.group_id))

    return flask.render_template('registration/upload_group_image.html', form =  form, 
            branch = Group)


@registration.route('/update_group_profile/<int:group_id>', methods = ['GET', 'POST'])
def update_group_profile(group_id):
    Group = group.query.filter_by(group_id = group_id).first()
    form = UpdateGroupProfileForm()

    if form.validate_on_submit():
        Group.name = form.name.data
        Group.location_address = form.location_address.data

        db.session.add(Group)
        db.session.commit()

        flask.flash('Profile update successful')
        return flask.redirect(
                flask.url_for('profiles.group_profile', group_id = Group.group_id))

    form.name.data = Group.name
    form.location_address.data = Group.location_address

    return flask.render_template('registration/update_group_profile.html', form = form,
            group = Group)


@registration.route('/register_member', methods = ['GET', 'POST'])
def register_member():
    form = RegisterMemberForm()
    
    countries_list = [((country.name), (country.name)) for country in iso3166.countries]
    form.nationality.choices = countries_list
    
    if form.validate_on_submit():
        Member = member(
                id_no = form.id_no.data,
                first_name = form.first_name.data,
                middle_name = form.middle_name.data,
                last_name = form.last_name.data,
                gender = form.gender.data,
                email_address = form.email_address.data,
                location_address = form.location_address.data,
                nationality = form.nationality.data,
        )
        db.session.add(Member)
        db.session.commit()

        if form.gender.data == "male":
            flask.flash(f"Mr. {form.first_name.data} registered successfully.")
        else:
            flask.flash(f"Ms {form.first_name.data} registered successfully.")

        return flask.redirect(flask.url_for('registration.register_member'))
    
    return flask.render_template('registration/register_member.html', form = form)


@registration.route('/select_group_member/<int:group_id>')
def select_group_member(group_id):
    Group = group.query.filter_by(group_id = group_id).first()

    page = flask.request.args.get('page', 1, type = int)
    pagination = member.query.filter_by(group_id = None)\
            .order_by(member.member_id.desc()).paginate(page, 
                flask.current_app.config['FLASKY_POSTS_PER_PAGE'], error_out = False)
    members = pagination.items

    return flask.render_template('registration/select_group_member.html', group = Group,
            pagination = pagination, members = members)


@registration.route('/add_member_group/<int:group_id>/<int:member_id>', 
        methods = ['GET', 'POST'])
def add_group_member(group_id, member_id):
    Member = member.query.filter_by(member_id = member_id).first()
    Member.group_id = group_id

    db.session.add(Member)
    db.session.commit()
    flask.flash(f'{Member.first_name} {Member.last_name} is a member of the group')
    return flask.redirect(flask.url_for('profiles.group_profile', group_id = group_id))


@registration.route('/change_group_status/<int:group_id>')
def change_group_status(group_id):
    dependencies.change_group_status(group_id)
    return flask.redirect(flask.url_for('profiles.list_of_groups'))


@registration.route('/change_user_status/<int:user_id>')
def change_user_status_m(user_id):
    dependencies.change_user_status(user_id)
    return flask.redirect(flask.url_for('profiles.list_of_users'))


@registration.route('/change_member_status/<int:member_id>')
def change_member_status_m(member_id):
    dependencies.change_member_status(member_id)
    return flask.redirect(flask.url_for('profiles.list_of_members'))


@registration.route('/change_member_status/<int:member_id>/<int:group_id>')
def change_member_status_g(member_id, group_id):
    dependencies.change_member_status(member_id)
    return flask.redirect(
            flask.url_for('profiles.group_profile', group_id = group_id))

@registration.route('/register_group', methods = ['GET', 'POST'])
def register_group():
    form = RegisterGroupForm()

    if form.validate_on_submit():
        Group = group(
                name = form.name.data,
                email_address = form.email_address.data,
                phone_no = form.phone_no.data,
                location_address = form.location_address.data
            )
        db.session.add(Group)
        db.session.commit()

        return flask.redirect(flask.url_for('registration.register_group'))
    return flask.render_template('registration/register_group.html', form = form)
