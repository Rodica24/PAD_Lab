from app import app, mongo, cache  # Import the components from the app
from flask import json
import unittest
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash  # Import the password hashing function


class TestUserService(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.mongo')
    def test_register_user(self, mock_mongo):
        # Mock successful registration
        mock_mongo.db.users.find_one.return_value = None  # No user found
        response = self.app.post('/register', json={
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 201)

    @patch('app.mongo')
    def test_register_existing_user(self, mock_mongo):
        # Mock an existing user
        mock_mongo.db.users.find_one.return_value = {'username': 'john_doe'}
        response = self.app.post('/register', json={
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 400)

    @patch('app.mongo')
    def test_get_user(self, mock_mongo):
        # Mock a user found in the database
        mock_mongo.db.users.find_one.return_value = {'username': 'john_doe', 'email': 'john@example.com'}
        response = self.app.get('/users/john_doe')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.mongo')
    def test_get_user_not_found(self, mock_mongo):
        # Mock no user found
        mock_mongo.db.users.find_one.return_value = None
        response = self.app.get('/users/john_doe')
        self.assertEqual(response.status_code, 404)


    @patch('app.mongo')
    def test_login_user_invalid_password(self, mock_mongo):
        # Mock an invalid password scenario
        mock_mongo.db.users.find_one.return_value = {
            '_id': 'user_id_123',
            'username': 'john_doe',
            'password': generate_password_hash('password')  # Correct password in DB
        }
        response = self.app.post('/login', json={
            'username': 'john_doe',
            'password': 'wrongpassword'  # Incorrect password
        })
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()
