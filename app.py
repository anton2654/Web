import numpy as np
import os
from flask import Flask, render_template, request, redirect, url_for, flash ,jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User , Task # Переконайся, що в models.py є поле progress у Task
import time
import json
import threading


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
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()

# --- МЕТОД ГАУСА (з прогресом та time.sleep) ---
def gaussian_elimination(app, task_id, a_matrix, b_vector): 
    def update_progress(progress_value):
         with app.app_context(): 
            task = db.session.get(Task, task_id)
            if task:
                task.progress = progress_value
                db.session.commit()
            print(f"[Thread-{task_id}] Progress updated to {progress_value}%") # Для дебагу

    # --- Початок ---
    a = np.copy(a_matrix).astype(float) 
    b = np.copy(b_vector).astype(float)
    n = len(b)
    update_progress(5) # Початковий прогрес

    # --- 1. Прямий хід (Forward Elimination) ---
    for k in range(n - 1):
        max_index = k + np.argmax(np.abs(a[k:, k]))
        if k != max_index:
             a[[k, max_index]] = a[[max_index, k]] 
             b[[k, max_index]] = b[[max_index, k]] 
        if abs(a[k, k]) < 1e-10: 
            raise np.linalg.LinAlgError("Матриця сингулярна (нульовий діагональний елемент після pivoting).")
            
        for i in range(k + 1, n):
            factor = a[i, k] / a[k, k]
            a[i, k:] = a[i, k:] - factor * a[k, k:] 
            b[i] = b[i] - factor * b[k]
            # --- ШТУЧНА ЗАТРИМКА ---
            if n > 1: time.sleep(2) # Робимо затримку меншою для великих матриць
            
        current_progress = 5 + int(((k + 1) / (n - 1)) * 45) if n > 1 else 50
        update_progress(min(current_progress, 50)) 

    update_progress(50) 
    
    if n > 0 and abs(a[n-1, n-1]) < 1e-10:
         raise np.linalg.LinAlgError("Матриця сингулярна після прямого ходу.")
            
    # --- 2. Зворотний хід (Back Substitution) ---
    x = np.zeros(n)
    for i in range(n - 1, -1, -1): 
        if n > 0 and abs(a[i, i]) < 1e-10: # Перевірка перед діленням
            raise ValueError("Нульовий діагональний елемент під час зворотного ходу.")
        sum_ax = np.dot(a[i, i + 1:], x[i + 1:])
        x[i] = (b[i] - sum_ax) / a[i, i] if n > 0 else 0 # Захист від ділення на нуль для n=0

        if n > 0: time.sleep(0.05 / n) 
        
        current_progress = 50 + int(((n - i) / n) * 49) if n > 0 else 99
        update_progress(min(current_progress, 99)) 

    x_rounded = np.round(x, 2)
    solution_str = ' '.join(map(str, x_rounded))

    update_progress(99) 
    
    return {
        "solution": solution_str,
    }
# --- КІНЕЦЬ МЕТОДУ ГАУСА ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (код без змін) ...
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
     # ... (код без змін) ...
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
    # ... (код без змін) ...
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # ... (код без змін) ...
    server_name = os.environ.get('SERVER_NAME', 'Невідомий сервер') 
    user_tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.timestamp.desc()).all()
    return render_template('index.html', server_name=server_name, tasks=user_tasks)


# Функція, яка буде виконувати обчислення у фоновому потоці
def run_calculation(app, task_id, matrix_a_str, vector_b_str):
    print(f"[Thread-{task_id}] Starting calculation...")
    
    # Створюємо тимчасові змінні для зберігання результату
    final_status = 'pending'
    final_result_gaussian = None
    final_progress = 0
    final_error = None

    try:
        # Нам потрібен app_context для оновлення прогресу всередині gaussian_elimination
        with app.app_context():
            # --- Парсинг і валідація ---
            print(f"[Thread-{task_id}] Parsing inputs...")
            try:
                a_rows_str = [row.strip() for row in matrix_a_str.strip().split('\n') if row.strip()]
                b_elements_str = vector_b_str.strip().split()
                if not a_rows_str: raise ValueError("Матриця A не може бути порожньою.")
                if not b_elements_str: raise ValueError("Вектор B не може бути порожнім.")
                A = np.array([list(map(float, row.split())) for row in a_rows_str])
                B = np.array(list(map(float, b_elements_str)))
            except (ValueError, TypeError) as parse_error:
                 print(f"[Thread-{task_id}] Parsing error: {parse_error}")
                 raise ValueError(f"Некоректний формат чисел: {parse_error}")

            print(f"[Thread-{task_id}] Validating dimensions...")
            n = A.shape[0]
            if n == 0: raise ValueError("Матриця не може бути порожньою після обробки.")
            if A.shape[1] != n or len(B) != n: raise ValueError("Матриця A має бути квадратною...")
            if n > MAX_MATRIX_SIZE: raise ValueError(f"Розмір матриці ({n}x{n}) перевищує...")

            # --- Виконання методу Гауса ---
            print(f"[Thread-{task_id}] Running Gaussian elimination...")
            # gaussian_elimination тепер оновлює прогрес в БД самостійно
            gaussian_result = gaussian_elimination(app, task.id, A, B) 
            results['gaussian'] = gaussian_result 
            print(f"[Thread-{task_id}] Calculation successful.")
            task.status = 'completed'

            task.result_gaussian = results['gaussian']['solution']

            task.progress = 100

    except Exception as e:
        # Якщо сталася помилка
        final_error = str(e)
        final_status = 'failed'
        final_progress = -1 
        print(f"[Thread-{task_id}] Calculation failed: {e}")

    finally:
        # --- Фінальний запис у БД ---
        # Створюємо НОВИЙ, чистий app_context *лише* для цього запису
        with app.app_context():
            try:
                # Отримуємо свіжий об'єкт Task з БД
                task = db.session.get(Task, task_id)
                if task:
                    # Оновлюємо його
                    task.status = final_status
                    task.result_gaussian = final_result_gaussian
                    task.progress = final_progress
                    task.error_message = final_error
                    # Зберігаємо зміни
                    db.session.commit()
                    print(f"[Thread-{task_id}] DB commit successful. Final status: {task.status}")
                else:
                    print(f"[Thread-{task_id}] Task not found in finally block.")
            except Exception as db_error:
                 print(f"[Thread-{task_id}] !!! DB commit FAILED: {db_error}")
                 db.session.rollback()

MAX_MATRIX_SIZE = 100

@app.route('/solve', methods=['POST'])
@login_required
def solve():
    # ... (код без змін) ...
    matrix_a_input = request.form.get('matrix_a', '')
    vector_b_input = request.form.get('vector_b', '')
    new_task = Task(
        input_matrix=matrix_a_input,
        input_vector=vector_b_input,
        user_id=current_user.id,
        status='pending' 
    )
    db.session.add(new_task)
    db.session.commit() 
    thread = threading.Thread(target=run_calculation, args=(app, new_task.id, matrix_a_input, vector_b_input))
    thread.start()
    flash(f'Завдання {new_task.id} додано в обробку.')
    return redirect(url_for('index'))


@app.route('/tasks_status')
@login_required
def tasks_status():
    # ... (код без змін) ...
    task_ids_str = request.args.get('ids')
    if not task_ids_str:
        return jsonify({"error": "No task IDs provided"}), 400
    try:
        task_ids = [int(id) for id in task_ids_str.split(',')]
    except ValueError:
        return jsonify({"error": "Invalid task IDs format"}), 400
    tasks = Task.query.filter(Task.user_id == current_user.id, Task.id.in_(task_ids)).all()
    status_map = {}
    for task in tasks:
        status_map[task.id] = {
            'status': task.status,
            'result_gaussian': task.result_gaussian, 
            'progress': task.progress,
            'error_message': task.error_message
        }
    return jsonify(status_map)

if __name__ == '__main__':
    app.run(debug=True)