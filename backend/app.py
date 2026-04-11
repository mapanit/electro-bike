from flask import Flask, request, jsonify # type: ignore
from flask_cors import CORS # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore
import pymysql
import os
import time
import sys
pymysql.install_as_MySQLdb()

app = Flask(__name__)

# CORS конфигурация
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3030')
CORS(app, resources={r"/api/*": {"origins": cors_origins.split(',')}})

# Конфигурация базы данных
db_host = os.getenv('DB_HOST', 'db')
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', 'root')
db_name = os.getenv('DB_NAME', 'mi')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 3600
}

db = SQLAlchemy(app)

# Функция для подождания готовности БД
def wait_for_db(max_retries=30, retry_interval=2):
    """Ждём, пока БД будет готова к подключению"""
    for attempt in range(max_retries):
        try:
            print(f"🔄 Попытка подключения к БД ({attempt + 1}/{max_retries})...", file=sys.stderr)
            with app.app_context():
                db.engine.connect()
            print("✅ БД готова!", file=sys.stderr)
            return True
        except Exception as e:
            print(f"⏳ БД не готова: {e}", file=sys.stderr)
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
            else:
                print("❌ Не удалось подключиться к БД после всех попыток", file=sys.stderr)
                return False
    return False


class User(db.Model):
    __tablename__ = 'users'  # Явно указываем имя таблицы
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)

class Feed(db.Model):
    __tablename__ = 'feedback'  # Явно указываем имя таблицы
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    feedback = db.Column(db.Text, nullable=False)


@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        # Проверка наличия всех необходимых полей
        if not all(key in data for key in ['email', 'password', 'name']):
            return jsonify({'error': 'Не все поля заполнены'}), 400

        # Проверка на пустые значения
        if not data['email'].strip() or not data['password'] or not data['name'].strip():
            return jsonify({'error': 'Поля не могут быть пустыми'}), 400

        # Проверка существующего пользователя
        if User.query.filter_by(email=data['email'].strip()).first():
            return jsonify({'error': 'Пользователь с таким email уже существует'}), 400

        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            email=data['email'].strip(),
            password=hashed_password,
            name=data['name'].strip()
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'message': 'Регистрация успешна',
            'name': new_user.name
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print("Registration error:", str(e))  # Для отладки
        return jsonify({'error': 'Ошибка при регистрации'}), 500


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if user and check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Login successful', 'name': user.name}), 200

    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/feedback', methods=['POST'])
def feedback():
    try:
        data = request.json
        
        # Проверка наличия всех необходимых полей
        if not all(key in data for key in ['name', 'feedback']):
            return jsonify({'error': 'Не все поля заполнены'}), 400

        # Проверка на пустые значения
        if not data['name'].strip() or not data['feedback'].strip():
            return jsonify({'error': 'Поля не могут быть пустыми'}), 400

        new_feedback = Feed(
            name=data['name'].strip(),
            feedback=data['feedback'].strip()
        )

        db.session.add(new_feedback)
        db.session.commit()

        return jsonify({
            'message': 'Отзыв успешно отправлен',
            'name': new_feedback.name
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print("Feedback error:", str(e))  # Для отладки
        return jsonify({'error': 'Ошибка при отправке отзыва'}), 500


@app.route('/api/feedback', methods=['GET'])
def get_feedbacks():
    try:
        feedbacks = Feed.query.all()
        return jsonify([{
            'id': feedback.id,
            'name': feedback.name,
            'feedback': feedback.feedback
        } for feedback in feedbacks]), 200
    except Exception as e:
        print("Get feedbacks error:", str(e))
        return jsonify({'error': 'Ошибка при получении отзывов'}), 500


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE,OPTIONS')
    return response


if __name__ == '__main__':
    # Ждём, пока БД будет готова
    if not wait_for_db():
        print("❌ Не удалось подключиться к БД. Выходим.", file=sys.stderr)
        sys.exit(1)
    
    # Создаём таблицы
    with app.app_context():
        try:
            db.create_all()
            print("✅ Таблицы инициализированы", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Ошибка при создании таблиц: {e}", file=sys.stderr)
    
    # Запускаем приложение
    port = int(os.getenv('PORT', 8030))
    print(f"🚀 Flask запускается на 0.0.0.0:{port}", file=sys.stderr)
    app.run(host='0.0.0.0', port=port, debug=False)
