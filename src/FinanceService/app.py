import sys
import json
from flask import Flask, jsonify, request
import asyncio
import websockets
from threading import Thread
from pymongo import MongoClient
from bson import ObjectId

# Initialize Flask app
app = Flask(__name__)

# MongoDB connection to the Finances database
finance_client = MongoClient('mongodb://localhost:27017/')
finance_db = finance_client['finances']
contributions_collection = finance_db['transactions']
groups_collection = finance_db['groups']

# MongoDB connection to the Users database (separate)
user_client = MongoClient('mongodb://localhost:27017/')
user_db = user_client['users']
users_collection = user_db['users']

# Get ports from command-line arguments
http_port = int(sys.argv[1]) if len(sys.argv) > 1 else 5003  # Default HTTP port
websocket_port = int(sys.argv[2]) if len(sys.argv) > 2 else 5001  # Default WebSocket port

# WebSocket handler function for group saving goals
async def group_saving_goal_handler(websocket, path):
    username = None
    group_name = None
    
    try:
        async for message in websocket:
            data = json.loads(message)  # Parse JSON instead of using eval
            print(f"Received message: {data}")

            if data['event'] == 'join':
                username = data['username']
                group_name = data['group_name']

                user = users_collection.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})
                if not user:
                    await websocket.send(f"User {username} not found!")
                    continue
                user_id = user['_id']

                group = groups_collection.find_one({"group_name": group_name})
                if not group:
                    await websocket.send(f"Group {group_name} not found!")
                    continue
                group_id = group['_id']

                print(f"User {username} joined group {group_name}")
                await websocket.send(f"User {username} joined group {group_name}")
            
            elif data['event'] == 'contribute':
                amount = data['amount']

                if not username or not group_name:
                    await websocket.send("You must join a group first.")
                    continue

                print(f"User {username} contributed {amount} to group {group_name}")

                contribution = {
                    'user_id': user_id,
                    'group_id': group_id,
                    'amount': amount
                }
                contributions_collection.insert_one(contribution)

                group = groups_collection.find_one({"_id": group_id})
                if group:
                    new_current_amount = group['current_amount'] + amount
                    groups_collection.update_one(
                        {"_id": group_id},
                        {"$set": {"current_amount": new_current_amount}}
                    )
                    print(f"Updated group {group_name}'s current amount to {new_current_amount}")

                await websocket.send(f"User {username} contributed {amount} to the group saving goal!")
    
    except websockets.exceptions.ConnectionClosed as e:
        print(f"User {username} disconnected from group {group_name}")

# Function to run the WebSocket server in its own thread
def run_websocket_server():
    print(f"Starting WebSocket server on port {websocket_port}...")
    asyncio.set_event_loop(asyncio.new_event_loop())
    start_server = websockets.serve(group_saving_goal_handler, "localhost", websocket_port)
    asyncio.get_event_loop().run_until_complete(start_server)
    print(f"WebSocket server running on ws://localhost:{websocket_port}")
    asyncio.get_event_loop().run_forever()

# REST Endpoints for Transactions and Status

@app.route('/status', methods=['GET'])
def status():
    total_transactions = contributions_collection.count_documents({})
    return jsonify({'status': f'Finance Service is running on HTTP port {http_port}', 'total_transactions': total_transactions}), 200

@app.route('/transactions', methods=['POST'])
def create_transaction():
    data = request.get_json()
    user_id = data.get('user_id')
    amount = data.get('amount')
    transaction_type = data.get('transaction_type')
    description = data.get('description')

    if not user_id or not amount or not transaction_type:
        return jsonify({'error': 'Missing required fields'}), 400

    transaction = {
        'user_id': ObjectId(user_id),
        'amount': amount,
        'transaction_type': transaction_type,
        'description': description
    }
    
    contributions_collection.insert_one(transaction)
    
    return jsonify({'message': 'Transaction created successfully'}), 201

@app.route('/transactions/<user_id>', methods=['GET'])
def get_transactions(user_id):
    try:
        transactions = list(contributions_collection.find({'user_id': ObjectId(user_id)}))
        if transactions:
            transaction_list = [{'id': str(t['_id']), 'amount': t['amount'], 'type': t['transaction_type'], 'description': t['description']} for t in transactions]
            return jsonify({'transactions': transaction_list}), 200
        else:
            return jsonify({'error': 'No transactions found for this user'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Main function to start both Flask and WebSocket servers
if __name__ == "__main__":
    # Start the WebSocket server in a separate thread
    websocket_thread = Thread(target=run_websocket_server)
    websocket_thread.start()

    # Start the Flask HTTP server on the provided HTTP port
    app.run(port=http_port)
