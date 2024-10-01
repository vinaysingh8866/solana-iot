import logging
import time
from threading import Thread
from datetime import datetime, timedelta
from . import w3, mqtt_client, db
from .models import Transaction, Session

wallet_address_to_monitor = '0xYourWalletAddressHere'.lower()

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
    from_address = tx['from']
    value_in_ether = w3.fromWei(tx['value'], 'ether')

    if value_in_ether >= 0.01:  # Example condition
        logging.info(f"Valid transaction of {value_in_ether} ETH from {from_address}")

        new_transaction = Transaction(
            wallet_address=tx['to'],
            amount=value_in_ether,
            tx_hash=tx_hash
        )
        db.session.add(new_transaction)
        db.session.commit()

        session_duration = 15
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=session_duration)

        new_session = Session(
            wallet_address=tx['to'],
            start_time=start_time,
            end_time=end_time,
            duration_minutes=session_duration,
            transaction_id=new_transaction.id
        )
        db.session.add(new_session)
        db.session.commit()

        mqtt_client.publish('emqx/esp8266', 'enable_device')
        logging.info("Device enabled via MQTT due to valid transaction")
    else:
        logging.info(f"Transaction of {value_in_ether} ETH is below the threshold")

def start_blockchain_listener():
    listener_thread = Thread(target=check_wallet_transactions)
    listener_thread.start()
