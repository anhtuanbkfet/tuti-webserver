from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .forms import UserForm
from .models import User
from . import db

auth = Blueprint('auth', __name__)

    
@auth.route('/login', methods=['POST', 'GET'])
def login():
    user_form = UserForm()

    if request.method == 'POST':
        # Get validated data from form
        username = user_form.username.data # You could also have used request.form['username']
        password = user_form.password.data # You could also have used request.form['password']
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        # check if user actually exists
        # take the user supplied password, hash it, and compare it to the hashed password in database
        if not user or not check_password_hash(user.password, password): 
            flash('Please check your login details and try again.')
            return render_template('login.html', form=user_form)

        # if the above check passes, then we know the user has the right credentials
        login_user(user, remember=remember)

        #return redirect_dest(home='main.index')
        return redirect(url_for('explorer.show_directory'))

    #flash('Type username and password to login', 'info')
    return render_template('login.html', form=user_form)


@auth.route('/signup', methods=['POST', 'GET'])
# @login_required
def signup():
    user_form = UserForm()

    if request.method == 'POST':
        # Get validated data from form
        name = user_form.name.data # You could also have used request.form['name']
        username = user_form.username.data # You could also have used request.form['username']
        password = user_form.password.data # You could also have used request.form['password']

        user = User.query.filter_by(username=username).first() # if this returns a user, then the email already exists in database
        
        if user: # if a user is found, we want to redirect back to signup page so user can try again  
            flash('This accout is already exists!')
            return redirect(url_for('auth.signup', form=user_form))
        #else
        # create new user with the form data. Hash the password so plaintext version isn't saved.
        new_user = User(username=username, name=name, password=generate_password_hash(password, method='sha256'))

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Your accout is have been registered!, Please login to use our Cemera allert service!')
        return redirect(url_for('auth.login', form=user_form))
    return render_template('signup.html', form=user_form)

@auth.route('/log-out')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

