import asyncio
import logging
from datetime import datetime, timedelta
from threading import Thread

from solders.pubkey import Pubkey
from solders.signature import Signature  # Import Signature
from solana.rpc.async_api import AsyncClient

from . import mqtt_client, db
from .models import Transaction, Session
from config import Config
import time
# Configuration
monitored_wallet_address = Config.MONITORED_WALLET
monitored_wallet_pubkey = Pubkey.from_string(monitored_wallet_address)
solana_rpc_endpoint = Config.SOLANA_RPC_ENDPOINT
print(monitored_wallet_pubkey)
async def check_wallet_transactions(app):
    async with AsyncClient(solana_rpc_endpoint) as client:
        last_signature = None
        while True:
            # try:
                print("in try")
                # Fetch confirmed signatures for the account
                resp = await client.get_signatures_for_address(
                    monitored_wallet_pubkey,
                    commitment='confirmed',
                    before=last_signature,
                    
                )
                # print(resp)
                signatures = resp.value
                if not signatures:
                    logging.info("No new signatures found.")
                else:
                    signature_info = signatures[0]
                    signature = signature_info.signature

                    # Convert signature to string for storage
                    signature_str = str(signature)

                    # Check for duplicate transaction
                    existing_tx = Transaction.query.filter_by(tx_hash=signature_str).first()
                    if existing_tx:
                        logging.info(f"Transaction {signature_str} already processed, skipping.")
                    else:
                        await process_transaction(signature_str, app, client)

                    # Update the last_signature to avoid processing the same transaction again
                    last_signature = signature

                # Wait for 1 second before polling again
                time.sleep(3)

            # except Exception as e:
            #     logging.error(f"Exception in check_wallet_transactions: {e}")
            #     await asyncio.sleep(1)
import json
async def process_transaction(signature_str, app, client):
    with app.app_context():
        # try:
            # Convert the signature string back to a Signature object
            
            signature_obj = Signature.from_string(signature_str)
            
            # Get the transaction details
            print("processing ")
            tx_resp = await client.get_transaction(
                signature_obj,  # Pass the Signature object
                encoding='jsonParsed',
                commitment='confirmed',
                max_supported_transaction_version=0
                
            )
            
            # print(tx_resp)
            tx = tx_resp.value.to_json()
            tx = json.loads(tx)
            print(tx)
            # {"slot":330936604,"transaction":{"signatures":["4t3gBURULH5GiJsrHxnt4Jugna31kG7QUXTN7CZZTV7kX9EdJEtYLt9RbVad1LsaCmpXWiaj9b5rpRfaPHhjtksA"],"message":{"accountKeys":[{"pubkey":"GRcfGGcTzKwyPQRRNTUDUkqcAFqVEqnWpgf9GThW6bNj","writable":true,"signer":true},{"pubkey":"8q8AFWpTgk9Up5hQmj1xoc3DTQgChfgdR6ciZDFUB7dw","writable":true,"signer":false},{"pubkey":"11111111111111111111111111111111","writable":false,"signer":false},{"pubkey":"ComputeBudget111111111111111111111111111111","writable":false,"signer":false}],"recentBlockhash":"9R3BRGJLDQYUFkxS1XkuDhEoMdtFHq63X8ziyKTDXSv3","instructions":[{"programId":"ComputeBudget111111111111111111111111111111","accounts":[],"data":"3atJtxCCtbsV"},{"programId":"ComputeBudget111111111111111111111111111111","accounts":[],"data":"Fj2Eoy"},{"program":"system","programId":"11111111111111111111111111111111","parsed":{"info":{"destination":"8q8AFWpTgk9Up5hQmj1xoc3DTQgChfgdR6ciZDFUB7dw","lamports":100000000,"source":"GRcfGGcTzKwyPQRRNTUDUkqcAFqVEqnWpgf9GThW6bNj"},"type":"transfer"}}],"addressTableLookups":null}},"meta":{"err":null,"status":{"Ok":null},"fee":85000,"preBalances":[1969985000,30000000,1,1],"postBalances":[1869900000,130000000,1,1],"innerInstructions":[],"logMessages":["Program ComputeBudget111111111111111111111111111111 invoke [1]","Program ComputeBudget111111111111111111111111111111 success","Program ComputeBudget111111111111111111111111111111 invoke [1]","Program ComputeBudget111111111111111111111111111111 success","Program 11111111111111111111111111111111 invoke [1]","Program 11111111111111111111111111111111 success"],"preTokenBalances":[],"postTokenBalances":[],"rewards":[]},"version":"legacy","blockTime":1728188747}
            if tx is None:
                logging.error(f"Transaction {signature_str} not found.")
                return

            #check for error
            if tx.get('error'):
                logging.error(f"Error fetching transaction {signature_str}: {tx['error']}")
                return
            

            # Process the transaction
            instructions = tx['transaction']['message']['instructions']
            
            for instruction in instructions:
                program = instruction.get('program')
                parsed = instruction.get('parsed')
                if program == 'system' and parsed and parsed.get('type') == 'transfer':
                    info = parsed['info']
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
                                tx_hash=signature_str  # Store the signature as a string in the DB
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
        # except Exception as e:
        #     logging.error(f"Exception in process_transaction: {e}")
        #     return

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
        with app.app_context():
            asyncio.run(check_wallet_transactions(app))

    listener_thread = Thread(target=run_event_loop)
    listener_thread.daemon = True  # Allows the thread to exit when the main program exits
    listener_thread.start()
