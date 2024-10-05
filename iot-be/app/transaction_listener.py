import asyncio
import logging
from datetime import datetime, timedelta
from threading import Thread
from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import AsyncWebsocketClient
from . import mqtt_client, db
from .models import Transaction, Session
from config import Config

monitored_wallet_address = Config.MONITORED_WALLET
monitored_wallet_pubkey = PublicKey(monitored_wallet_address)
solana_rpc_endpoint = Config.SOLANA_RPC_ENDPOINT

async def check_wallet_transactions(app):
    async with AsyncWebsocketClient(Config.SOLANA_WS_ENDPOINT) as websocket:
        subscription_id = await websocket.account_subscribe(monitored_wallet_pubkey)
        logging.info(f"Subscribed to account {monitored_wallet_address} with subscription ID {subscription_id}")

        while True:
            response = await websocket.recv()
            await process_wallet_transaction(response, app)

async def process_wallet_transaction(response, app):
    with app.app_context():
        if 'result' in response and 'value' in response['result']:
            account_info = response['result']['value']
            # Implement logic based on the account info received
            await fetch_and_process_transactions(app)

async def fetch_and_process_transactions(app):
    async with AsyncClient(solana_rpc_endpoint) as client:
        # Fetch confirmed signatures for the account
        signatures_resp = await client.get_signatures_for_address(
            monitored_wallet_pubkey,
            limit=1,
            commitment='confirmed'
        )
        signatures = signatures_resp['result']
        if not signatures:
            logging.info("No new signatures found.")
            return

        signature_info = signatures[0]
        signature = signature_info['signature']

        # Check for duplicate transaction
        existing_tx = Transaction.query.filter_by(tx_hash=signature).first()
        if existing_tx:
            logging.info(f"Transaction {signature} already processed, skipping.")
            return

        # Get the transaction details
        tx_response = await client.get_transaction(
            signature,
            encoding='jsonParsed',
            commitment='confirmed'
        )
        tx = tx_response['result']
        if not tx:
            logging.error(f"Transaction {signature} not found.")
            return

        # Check if the transaction was successful
        if tx['meta']['err'] is not None:
            logging.info(f"Transaction {signature} failed.")
            return

        # Process the transaction
        instructions = tx['transaction']['message']['instructions']

        for instruction in instructions:
            if instruction['program'] == 'system' and instruction['parsed']['type'] == 'transfer':
                info = instruction['parsed']['info']
                source_account = info['source']
                dest_account = info['destination']
                lamports = int(info['lamports'])

                if dest_account == monitored_wallet_address:
                    value_in_sol = lamports / 1e9  # Convert lamports to SOL
                    from_address = source_account

                    # Check for valid transaction amount
                    if value_in_sol >= 0.01:  # Example threshold
                        logging.info(f"Valid transaction of {value_in_sol} SOL from {from_address}")

                        # Save the transaction in the database
                        new_transaction = Transaction(
                            wallet_address=dest_account,
                            amount=value_in_sol,
                            tx_hash=signature
                        )
                        db.session.add(new_transaction)
                        db.session.commit()

                        # Calculate session time (15 minutes as an example)
                        session_duration = 15
                        start_time = datetime.utcnow()
                        end_time = start_time + timedelta(minutes=session_duration)

                        # Save the session in the database
                        new_session = Session(
                            wallet_address=dest_account,
                            start_time=start_time,
                            end_time=end_time,
                            duration_minutes=session_duration,
                            transaction_id=new_transaction.id
                        )
                        db.session.add(new_session)
                        db.session.commit()

                        # Enable the device asynchronously via MQTT
                        publish_device_enable(app)
                    else:
                        logging.info(f"Transaction of {value_in_sol} SOL is below the threshold")
                    return

def publish_device_enable(app):
    with app.app_context():
        try:
            mqtt_client.publish('emqx/esp8266', 'enable_device')
            logging.info("Device enabled via MQTT")
        except Exception as e:
            logging.error(f"Error publishing MQTT message: {e}")

def start_blockchain_listener(app):
    # Run the event loop in a new thread
    def run_event_loop():
        asyncio.run(check_wallet_transactions(app))

    listener_thread = Thread(target=run_event_loop)
    listener_thread.daemon = True  # Optional: allows the thread to exit when the main program exits
    listener_thread.start()
