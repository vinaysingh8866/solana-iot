import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # MQTT Configuration
    MQTT_BROKER_URL = os.getenv('MQTT_BROKER_URL', 'v012a1b1.ala.us-east-1.emqxsl.com')
    MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', 8883))  # Port for TLS
    MQTT_USERNAME = os.getenv('MQTT_USERNAME', 'backend')
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', 'backend')
    MQTT_KEEPALIVE = int(os.getenv('MQTT_KEEPALIVE', 5))
    MQTT_TLS_ENABLED = True
    MQTT_TLS_CA_CERTS = os.getenv('MQTT_TLS_CA_CERTS', 'ca_certificate.crt')
    MQTT_TLS_VERSION = 2

    # SQLAlchemy Database Configuration (using SQLite)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Web3 Configuration
    WEB3_PROVIDER = os.getenv('WEB3_PROVIDER', 'https://YOUR_INFURA_OR_ALCHEMY_ENDPOINT')
    MONITORED_WALLET = os.getenv('MONITORED_WALLET', '0xYourWalletAddressHere').lower()
    TRANSACTION_CONFIRMATIONS = int(os.getenv('TRANSACTION_CONFIRMATIONS', 3))  # Wait for 3 confirmations
