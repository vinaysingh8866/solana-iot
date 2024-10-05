from flask import Blueprint, request, jsonify
from . import mqtt_client, db
from .models import Transaction, Session

bp = Blueprint('routes', __name__)

# MQTT publish route
@bp.route('/publish', methods=['POST'])
def publish_message():
    request_data = request.get_json()
    if not request_data or 'topic' not in request_data or 'msg' not in request_data:
        return jsonify({'error': 'Invalid request'}), 400

    publish_result = mqtt_client.publish(request_data['topic'], request_data['msg'])
    if publish_result[0] == 0:
        return jsonify({'message': 'Message published successfully'}), 200
    else:
        return jsonify({'error': 'Failed to publish message'}), 500

# Retrieve transactions by wallet address
@bp.route('/transactions/<wallet_address>', methods=['GET'])
def get_transactions(wallet_address):
    transactions = Transaction.query.filter_by(wallet_address=wallet_address).all()
    return jsonify([{
        'id': tx.id,
        'wallet_address': tx.wallet_address,
        'amount': tx.amount,
        'timestamp': tx.timestamp.isoformat(),
        'tx_hash': tx.tx_hash
    } for tx in transactions])

# Retrieve sessions by wallet address
@bp.route('/sessions/<wallet_address>', methods=['GET'])
def get_sessions(wallet_address):
    sessions = Session.query.filter_by(wallet_address=wallet_address).all()
    return jsonify([{
        'id': session.id,
        'wallet_address': session.wallet_address,
        'start_time': session.start_time.isoformat(),
        'end_time': session.end_time.isoformat(),
        'duration_minutes': session.duration_minutes,
        'transaction_id': session.transaction_id
    } for session in sessions])
