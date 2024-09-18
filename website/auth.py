#login route is in auth
from functools import wraps
from flask import Blueprint, render_template, request,redirect, url_for, flash , session 
from .models import User
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user #to restrict access only to loged user

authBluprint = Blueprint('authBluprint',__name__)

@authBluprint.route('/login', methods=['GET', 'POST']) 
def login() :
    if request.method == 'POST' :
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email = email).first()
        if user :
            if check_password_hash(user.password, password) :
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                session['user_id'] = str(user.id)
                return redirect(url_for('viewsBluprint.home'))
            else :
                flash('Incorrect password, try again.', category='error')
        else :
            flash('Email  does not exist.', category='error')         
    return render_template("login.html", user = current_user)

@authBluprint.route('/logout')
@login_required
def logout(): 
    logout_user()
    return redirect(url_for('authBluprint.login'))

@authBluprint.route('/sign_up', methods=['GET', 'POST'])
def signUp() :
    if request.method =='POST': 
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')
        department = request.form.get('department')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        
        teacher = User.query.filter_by(email = email).first()
        if teacher : 
            flash ('Email address already exist.', category='error')
        elif len(email) < 4 :
            flash('Email must be greater than 4 characters', category='error')
        elif len(firstName) < 2: 
            flash('FirstName must be greater than 2 characters', category='error')
        elif len(lastName) <  2:
             flash('LastName must be greater than 2 characters', category='error')
        elif len(department) < 1: 
            flash('Department must be greater than 1 characters', category='error')
        elif len(password1) < 7:
            flash('Password must contain at leats 7 characters', category='error')
        elif password1 != password2:
            flash('Password do not match', category='error')
        else:
            #add user to database
            new_teacher = User(email=email, first_name = firstName, last_name = lastName, password = generate_password_hash(password1, method='sha256'), department = department,is_teacher=True)
            db.session.add(new_teacher)
            db.session.commit()
            login_user(new_teacher, remember=True)
            session['user_id'] = str(new_teacher.id)
            flash('Account created', category='success')
            return redirect(url_for('viewsBluprint.home'))
    return render_template("signup.html", user = current_user)

def teacherRequired(func):
    @wraps(func)
    @login_required
    def decorated_view(*args, **kwargs):
        if not current_user.is_teacher:
            return redirect(url_for('viewsBluprint.home'))
        return func(*args, **kwargs)
    return decorated_view