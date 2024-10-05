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

    # Solana Configuration
    SOLANA_RPC_ENDPOINT = os.getenv('SOLANA_RPC_ENDPOINT', 'https://api.mainnet-beta.solana.com')
    SOLANA_WS_ENDPOINT = os.getenv('SOLANA_WS_ENDPOINT', 'wss://api.mainnet-beta.solana.com')
    MONITORED_WALLET = os.getenv('MONITORED_WALLET', 'YourSolanaWalletAddressHere')
