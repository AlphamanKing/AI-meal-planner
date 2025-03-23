from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models.user import User
from app.utils.forms import RegistrationForm, LoginForm, UserProfileForm
from app.utils.helpers import save_profile_picture

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if user.is_admin:
                return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UserProfileForm(original_username=current_user.username, original_email=current_user.email)
    
    if form.validate_on_submit():
        # Update username and email
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        # Update profile picture if provided
        if form.profile_picture.data:
            picture_file = save_profile_picture(form.profile_picture.data)
            current_user.profile_picture = picture_file
        
        # Update password if provided
        if form.current_password.data and form.new_password.data:
            # Verify current password
            if bcrypt.check_password_hash(current_user.password, form.current_password.data):
                # Hash and set new password
                current_user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            else:
                flash('Current password is incorrect.', 'danger')
                return render_template('auth/profile.html', title='My Profile', form=form)
        
        # Save changes
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('auth.profile'))
    
    # Fill form with current user data
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    # Check if profile_picture is set and exists in profile_pics folder
    if current_user.profile_picture and current_user.profile_picture != 'default.jpg':
        profile_image = url_for('static', filename=f'img/profile_pics/{current_user.profile_picture}')
    else:
        # Use default image from images folder
        profile_image = url_for('static', filename='images/default.png')
    
    return render_template('auth/profile.html', title='My Profile', form=form, profile_image=profile_image) 