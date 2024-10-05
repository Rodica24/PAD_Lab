from flask import Flask, jsonify, request
import redis
import asyncio
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

cache = redis.Redis(host='localhost', port=6379)

active_users_count = 0
semaphore = asyncio.Semaphore(5)
timeout_duration = 5

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

with app.app_context():
    db.create_all()

@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'User Service is running', 'active_users': active_users_count}), 200

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    try:
        cached_user = cache.get(f"user:{id}")
        if cached_user:
            return jsonify({'source': 'cache', 'username': cached_user.decode('utf-8')}), 200

        user = User.query.get(id)
        if user:
            cache.set(f"user:{user.id}", user.username)
            return jsonify({'source': 'database', 'id': user.id, 'username': user.username, 'email': user.email}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

async def handle_user_request(data):
    async with semaphore:
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return {'error': 'Username, email, and password are required'}, 400

        hashed_password = generate_password_hash(password)

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        cache.set(f"user:{new_user.id}", new_user.username)

        await asyncio.sleep(1)

        return {'message': f'User {new_user.username} registered successfully'}

@app.route('/register', methods=['POST'])
async def register_user():
    data = request.get_json()

    try:
        async with semaphore:
            await asyncio.wait_for(handle_user_request(data), timeout=timeout_duration)
            global active_users_count
            active_users_count += 1  # Increment active user count
            return jsonify({'message': 'User registered successfully'}), 201
    except asyncio.TimeoutError:
        return jsonify({'error': 'Request timed out, please try again.'}), 408
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
async def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        cache.set('logged_in_user', user.id)
        return jsonify({
            'message': f'User {user.username} logged in successfully',
            'id': user.id
        }), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401


if __name__ == '__main__':
    app.run(port=5000)
