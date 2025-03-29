from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.extensions import db
from app.utils.helper import random_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        user = User.query.get(user_id)
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('room.room_list'))
        flash('ユーザーIDまたはパスワードが違います')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form['user_id']
        if User.query.get(user_id):
            flash('ユーザーIDは既に存在します')
        else:
            password = random_password()
            user = User(id=user_id)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return render_template('auth/register.html', password=password)
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
