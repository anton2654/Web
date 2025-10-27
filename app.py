import numpy as np
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User


app = Flask(__name__) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:2392697000@localhost:5432/matrix_db' 
app.config['SECRET_KEY'] = 'a-very-secret-key'

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

#МЕТОД ГАУСА
def gaussian_elimination(a_matrix, b_vector):
    a = np.copy(a_matrix).astype(float) # Працюємо з копіями
    b = np.copy(b_vector).astype(float)
    n = len(b)
    
    #1. Прямий хід (Forward Elimination)
    for k in range(n - 1):
        if abs(a[k, k]) < 1e-10: 
            found_pivot = False
            for i in range(k + 1, n):
                if abs(a[i, k]) > 1e-10:
                    a[[k, i]] = a[[i, k]] 
                    b[[k, i]] = b[[i, k]] 
                    found_pivot = True
                    break
            if not found_pivot:
                 raise np.linalg.LinAlgError("Матриця сингулярна або вимагає складнішого pivoting.")
                 
        for i in range(k + 1, n):
            if a[k, k] == 0: 
                 raise np.linalg.LinAlgError("Нульовий діагональний елемент після pivoting.")
            factor = a[i, k] / a[k, k]
            a[i, k:] = a[i, k:] - factor * a[k, k:]
            b[i] = b[i] - factor * b[k]
        
    if abs(a[n-1, n-1]) < 1e-10:
         raise np.linalg.LinAlgError("Матриця сингулярна після прямого ходу.")

    # Зворотний хід (Back Substitution) 
    x = np.zeros(n)
    for i in range(n - 1, -1, -1): 
        if a[i, i] == 0:
             raise ValueError("Нульовий діагональний елемент під час зворотного ходу.")
        sum_ax = np.dot(a[i, i + 1:], x[i + 1:])
        x[i] = (b[i] - sum_ax) / a[i, i]

    return {
        "solution": x.tolist()
    }


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            return redirect(url_for('index'))
        else:
            flash('Неправильний логін або пароль.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Користувач з таким іменем вже існує.')
            return redirect(url_for('register'))

        if password != password2:
            flash("Паролі не збігаються!")
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


MAX_MATRIX_SIZE = 100

@app.route('/solve', methods=['POST'])
@login_required
def solve():
    server_name = os.environ.get('SERVER_NAME', 'Невідомий сервер') 
    results = {} 
    error_message = None

    try:
        matrix_a_str = request.form.get('matrix_a')
        vector_b_str = request.form.get('vector_b')

        try:
            a_rows_str = [row.strip() for row in matrix_a_str.strip().split('\n') if row.strip()]
            b_elements_str = vector_b_str.strip().split()

            if not a_rows_str or not b_elements_str:
                 raise ValueError("Матриця або вектор порожні.")

            A = np.array([list(map(float, row.split())) for row in a_rows_str])
            B = np.array(list(map(float, b_elements_str)))
        except ValueError:
            raise ValueError("Некоректний формат чисел у матриці або векторі.")

        n = A.shape[0]
        if n == 0:
             raise ValueError("Матриця не може бути порожньою.")
        if A.shape[1] != n or len(B) != n:
            raise ValueError("Матриця A має бути квадратною, а її розмірність повинна збігатися з розмірністю вектора B.")
        
        if n > MAX_MATRIX_SIZE:
             raise ValueError(f"Розмір матриці ({n}x{n}) перевищує максимально допустимий ({MAX_MATRIX_SIZE}x{MAX_MATRIX_SIZE}).")

        try:
            solution_np = np.linalg.solve(A, B)
            results['numpy'] = {"solution": solution_np.tolist()}
        except np.linalg.LinAlgError as e:
            raise ValueError(f"Матриця є сингулярною або близькою до неї (помилка NumPy: {e})") 
        results['gaussian'] = gaussian_elimination(A, B) 

    except Exception as e:
        error_message = f"Помилка обробки: {e}"

    return render_template('result.html', 
                           results=results, 
                           error=error_message, 
                           server_name=server_name)



if __name__ == '__main__':
    app.run(debug=True)