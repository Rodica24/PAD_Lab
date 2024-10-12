import sys
import time
import grpc
from concurrent import futures
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import redis
from bson import ObjectId
import os
import logging
import user_service_pb2_grpc  # Import the generated gRPC code
import user_service_pb2  # Import the generated gRPC messages
from threading import Thread

# Initialize Flask app
app = Flask(__name__)

# MongoDB configuration
app.config['MONGO_URI'] = 'mongodb://localhost:27017/users'
mongo = PyMongo(app)

# Redis configuration
cache = redis.Redis(host='localhost', port=6379)

# Use environment variable for the port, or default to 5000
port = int(os.getenv("PORT", 5000))

# Set up logging
logging.basicConfig(level=logging.INFO)

# Request counting variables for health monitoring
request_counter = 0
start_time = time.time()
CRITICAL_LOAD_THRESHOLD = 60  # Define critical load, e.g., 60 requests per second

# Helper function to check if load is critical
def check_critical_load():
    global request_counter, start_time
    current_time = time.time()
    elapsed_time = current_time - start_time

    # If a second has passed, check the load
    if elapsed_time >= 1:
        if request_counter > CRITICAL_LOAD_THRESHOLD:
            logging.warning(f"Critical Load Alert: {request_counter} requests in the last second")
            # You can add more actions here, e.g., sending an email or Slack alert
        request_counter = 0
        start_time = current_time

@app.before_request
def before_request():
    global request_counter
    request_counter += 1
    check_critical_load()

# Flask API Endpoints
@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': f'User Service is running on port {port}'}), 200

@app.route('/users/<string:username>', methods=['GET'])
def get_user(username):
    user = mongo.db.users.find_one({'username': username})
    if user:
        return jsonify({'source': 'database', 'username': user['username'], 'email': user['email']}), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = generate_password_hash(data.get('password'))

    if mongo.db.users.find_one({'username': username}):
        return jsonify({'error': 'User already exists'}), 400

    mongo.db.users.insert_one({'username': username, 'email': email, 'password': password})
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = mongo.db.users.find_one({'username': username})

    if user and check_password_hash(user['password'], password):
        user_id_str = str(user['_id'])  # Convert ObjectId to string
        cache.set('logged_in_user', user_id_str)  # Store the user_id in Redis as a string
        return jsonify({
            'message': f'User {user["username"]} logged in successfully',
            'id': user_id_str  # Return user_id as a string
        }), 200
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

# Implement the gRPC Service class
class UserServicer(user_service_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        # Logic for fetching a user through gRPC
        user = mongo.db.users.find_one({'username': request.username})
        if user:
            return user_service_pb2.GetUserResponse(
                username=user['username'],
                email=user['email'],
                message='User found'
            )
        else:
            context.set_details('User not found')
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return user_service_pb2.GetUserResponse(message="User not found")

# gRPC Health Check Service (Optional, in case you want to monitor gRPC service health)
class HealthServicer(user_service_pb2_grpc.HealthServicer):
    def Check(self, request, context):
        return user_service_pb2.HealthCheckResponse(status=user_service_pb2.HealthCheckResponse.SERVING)

# Run gRPC Server in a separate thread
def serve_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(UserServicer(), server)
    server.add_insecure_port('[::]:50051')  # gRPC server listens on port 50051
    print("Starting gRPC server on port 50051...")
    server.start()
    server.wait_for_termination()

# Run Flask and gRPC in parallel
if __name__ == '__main__':
    grpc_thread = Thread(target=serve_grpc)
    grpc_thread.start()
    print(f"Starting UserService on port {port}")
    app.run(port=port)
