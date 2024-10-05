from flask import Flask, jsonify, request
import redis
import asyncio
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finances.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

cache = redis.Redis(host='localhost', port=6379)

total_transactions_count = 0
semaphore = asyncio.Semaphore(5)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Transaction {self.id} - {self.transaction_type} for User {self.user_id}>'

with app.app_context():
    db.create_all()

@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'Finance Service is running', 'total_transactions': total_transactions_count}), 200

async def handle_finance_request(data):
    async with semaphore:
        user_id = cache.get('logged_in_user')  # Get logged-in user ID
        
        if not user_id:
            return {'error': 'User not logged in'}, 403
        
        amount = data.get('amount')
        transaction_type = data.get('transaction_type')
        description = data.get('description')

        if not amount or not transaction_type:
            return {'error': 'Amount and transaction type are required'}, 400

        if transaction_type not in ['income', 'expense']:
            return {'error': 'Transaction type must be either "income" or "expense"'}, 400

        new_transaction = Transaction(user_id=int(user_id), amount=amount, transaction_type=transaction_type, description=description)
        db.session.add(new_transaction)
        db.session.commit()

        global total_transactions_count
        total_transactions_count += 1

        await asyncio.sleep(1)

        return {'message': f'Transaction {new_transaction.id} created successfully'}, 201

@app.route('/transactions', methods=['POST'])
async def create_transaction():
    data = request.get_json()
    
    if not semaphore.locked():
        result, status_code = await handle_finance_request(data)
        return jsonify(result), status_code
    else:
        return jsonify({'error': 'Too many concurrent requests, please try again later.'}), 429

@app.route('/transactions/<int:user_id>', methods=['GET'])
def get_transactions(user_id):
    try:
        cached_transactions = cache.get(f"transactions:user:{user_id}")
        if cached_transactions:
            return jsonify({'source': 'cache', 'transactions': cached_transactions.decode('utf-8')}), 200

        transactions = Transaction.query.filter_by(user_id=user_id).all()

        if transactions:
            transaction_list = [{'id': t.id, 'amount': t.amount, 'type': t.transaction_type, 'description': t.description} for t in transactions]
            cache.set(f"transactions:user:{user_id}", str(transaction_list))

            return jsonify({'source': 'database', 'transactions': transaction_list}), 200
        else:
            return jsonify({'error': 'No transactions found for this user'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001)
