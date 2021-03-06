from flask import render_template, flash, redirect, url_for, request, current_app
from .forms import RegistrationForm, LoginForm, PasswordResetRequestForm, PasswordResetForm, ChangePasswordForm
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User
from flask_mail import Mail, Message
from .tasks import send_email
from . import auth

#authgwy = Blueprint('authgwy', __name__, template_folder='templates')


@auth.before_app_request
def before_request():
	"""
	Executes before a request is processed.

	If will fire if four conditions are met:
		1. The user is authenticated (logged in)
		2. The user is not confirmed
		3. The request.endpoint is outside of the blueprint.
		4. The request.endpoint is not for a static resource.
	"""
	if current_user.is_authenticated \
			and not current_user.confirmed \
			and request.endpoint and request.endpoint[:5] != 'auth.' \
			and request.endpoint != 'static':
		print("endpoint is: " + request.endpoint)
		return redirect(url_for('auth.unconfirmed'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
	# route used for registering new Users. Validates register on submit, else returns the template for registration.
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(email=form.email.data, username=form.username.data, password=form.password.data)
		token = user.generate_confirmation_token()
		send_email(user.email, 'Confirm Your Account',
                   'auth/email/confirm', user=user, token=token)
		db.session.add(user)
		db.session.commit()
		flash('A confirmation email has been sent to you by email.')
		return redirect(url_for('auth.login'))
	return render_template('auth/register.html', form=form)

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
	# route used for logging in. Validates on submit and uses flask_logins 'login_user', else returns template for login.
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user, form.remember_me.data)
			return redirect(request.args.get('next') or url_for('main.index'))
		flash('Invalid email or password.')
	return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
	# logout user.
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
	if current_user.confirmed:
		return redirect(url_for('main.index'))
	if current_user.confirm(token):
		flash('You have confirmed your account. Thank you!')
	else:
		flash('The confirmation link has expired or is invalid.')
	return redirect(url_for('main.index'))

@auth.route('/confirm')
@login_required
def resend_confirmation():
	token = current_user.generate_confirmation_token()
	send_email(current_user.email, 'Confirm Your Account',
                   'auth/email/confirm', user=current_user, token=token)
	flash('A new confirmation email has been sent to you!')
	return redirect(url_for('main.index'))

@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	form = PasswordResetRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			token = user.generate_reset_token()
			send_email(user.email, 'Reset Your Password',
                   'auth/email/reset_password', user=user, token=token, next=request.args.get('next'))
		flash('An email has been sent to you with instructions on how to reset your password!')
		return redirect(url_for('auth.login'))
	return render_template('auth/reset_password.html', form=form)

@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	form = PasswordResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is None:
			return redirect(url_for('main.index'))
		if user.reset_password(token, form.password.data):
			flash('Your password has been updated!')
			return redirect(url_for('auth.login'))
		else:
			return redirect(url_for('main.index'))
	return render_template('auth/reset_password.html', form=form)

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
	form = ChangePasswordForm()
	if form.validate_on_submit():
		if current_user.verify_password(form.old_password.data):
			current_user.password = form.password.data
			db.session.add(current_user)
			flash('Your password has been updated!')
			return redirect(url_for('main.index'))
		else:
			flash('Invalid Password.')
	return render_template("auth/change_password.html", form=form)





















