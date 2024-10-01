from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mqtt import Mqtt
from flask_migrate import Migrate
from config import Config
from web3 import Web3

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLAlchemy, MQTT, Web3
db = SQLAlchemy(app)
mqtt_client = Mqtt(app)
migrate = Migrate(app, db)

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(app.config['WEB3_PROVIDER']))

# Import the models and routes
from app import models, routes, transaction_listener

@app.before_first_request
def create_tables():
    db.create_all()

# Start the blockchain listener in a thread
transaction_listener.start_blockchain_listener()
