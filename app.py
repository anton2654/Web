import numpy as np
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
import os

app = Flask(__name__)

# 'postgresql://КОРИСТУВАЧ:ПАРОЛЬ@ХОСТ:ПОРТ/НАЗВА_БД'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:2392697000@localhost:5432/matrix_db'
app.config['SECRET_KEY'] = 'a-very-secret-key'

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user , remember=remember)
            return redirect(url_for('index'))
        else:
            flash('Неправильний логін або пароль.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Користувач з таким іменем вже існує.')
            return redirect(url_for('register'))

        if password != confirm_password :
            flash("Passwords are not equal!")
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Реєстрація успішна! Тепер ви можете увійти.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    server_name = os.environ.get('SERVER_NAME', 'Невідомий сервер') 

    return render_template('index.html', server_name=server_name)

@app.route('/solve', methods=['POST'])
@login_required
def solve():
    server_name = os.environ.get('SERVER_NAME', 'Невідомий сервер')
    try:
        matrix_a_str = request.form.get('matrix_a')
        vector_b_str = request.form.get('vector_b')

        a_rows = matrix_a_str.strip().split('\n')
        A = [list(map(float, row.split())) for row in a_rows]
        A = np.array(A)

        b = list(map(float, vector_b_str.strip().split()))
        b = np.array(b)
        
        if A.shape[0] != A.shape[1] or A.shape[0] != len(b):
            raise ValueError("Розмірності матриці А та вектора b не сумісні.")

        solution = np.linalg.solve(A, b)
        return render_template('result.html', solution=solution, server_name=server_name)

    except Exception as e:
        error_message = f"Помилка: {e}"
        return render_template('result.html', error=error_message, server_name=server_name)

@app.route('/api/userinfo')
def user_info():
    if 'Authorization' in request.headers:
        api_key = request.headers['Authorization'].replace('Bearer ', '', 1)
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "api_key": user.api_key 
            }
        else:
            return {"error": "Invalid API Key"}, 401
    else:
        return {"error": "Authorization header is missing"}, 401

if __name__ == '__main__':
    app.run(debug=True)