from flask import render_template, redirect, request, url_for, Blueprint
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash

from models import User

auth = Blueprint('auth', __name__, template_folder='templates', static_folder='static')


# Маршрут для логіну
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin.index'))  # Перенаправлення на адмін-панель після успішного логіну
        else:
            return 'Invalid credentials', 403  # Помилка при неправильному логіні

    return render_template('admin/login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
