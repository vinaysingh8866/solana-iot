import logging
import time
from threading import Thread
from datetime import datetime, timedelta
from web3.exceptions import TransactionNotFound
from . import w3, mqtt_client, db
from .models import Transaction, Session
from config import Config

wallet_address_to_monitor = Config.MONITORED_WALLET

def check_wallet_transactions():
    latest_checked_block = w3.eth.get_block_number()

    while True:
        try:
            current_block = w3.eth.get_block_number()

            for block_number in range(latest_checked_block + 1, current_block + 1):
                block = w3.eth.get_block(block_number, full_transactions=True)

                for tx in block.transactions:
                    if tx['to'] and tx['to'].lower() == wallet_address_to_monitor:
                        logging.info(f"New transaction detected to wallet {wallet_address_to_monitor}: {tx}")
                        process_wallet_transaction(tx)

            latest_checked_block = current_block
            time.sleep(15)

        except Exception as e:
            logging.error(f"Error in checking wallet transactions: {e}")
            time.sleep(5)

def process_wallet_transaction(tx):
    tx_hash = tx['hash'].hex()

    # Check for duplicate transaction
    existing_tx = Transaction.query.filter_by(tx_hash=tx_hash).first()
    if existing_tx:
        logging.info(f"Transaction {tx_hash} already processed, skipping.")
        return

    # Wait for transaction confirmations
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120, block_identifier='latest')
        if receipt['status'] != 1:  # Check if the transaction was successful
            logging.info(f"Transaction {tx_hash} failed.")
            return
        confirmations = w3.eth.block_number - receipt['blockNumber']
        if confirmations < Config.TRANSACTION_CONFIRMATIONS:
            logging.info(f"Transaction {tx_hash} not yet confirmed ({confirmations} confirmations), skipping.")
            return
    except TransactionNotFound:
        logging.error(f"Transaction {tx_hash} not found.")
        return
    except Exception as e:
        logging.error(f"Error waiting for transaction {tx_hash}: {e}")
        return

    from_address = tx['from']
    value_in_ether = w3.fromWei(tx['value'], 'ether')

    # Check for valid transaction amount
    if value_in_ether >= 0.01:  # Example condition
        logging.info(f"Valid transaction of {value_in_ether} ETH from {from_address}")

        # Save the transaction in the database
        new_transaction = Transaction(
            wallet_address=tx['to'],
            amount=value_in_ether,
            tx_hash=tx_hash
        )
        db.session.add(new_transaction)
        db.session.commit()

        # Calculate session time (15 minutes as an example)
        session_duration = 15
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=session_duration)

        # Save the session in the database
        new_session = Session(
            wallet_address=tx['to'],
            start_time=start_time,
            end_time=end_time,
            duration_minutes=session_duration,
            transaction_id=new_transaction.id
        )
        db.session.add(new_session)
        db.session.commit()

        # Enable the device asynchronously via MQTT
        publish_device_enable()
    else:
        logging.info(f"Transaction of {value_in_ether} ETH is below the threshold")


def publish_device_enable():
    try:
        mqtt_client.publish('emqx/esp8266', 'enable_device')
        logging.info("Device enabled via MQTT")
    except Exception as e:
        logging.error(f"Error publishing MQTT message: {e}")

def start_blockchain_listener():
    listener_thread = Thread(target=check_wallet_transactions)
    listener_thread.start()
