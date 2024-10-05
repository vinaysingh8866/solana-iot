from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mqtt import Mqtt
from flask_migrate import Migrate
from config import Config
import logging

db = SQLAlchemy()
mqtt_client = Mqtt()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    mqtt_client.init_app(app)
    migrate.init_app(app, db)

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )

    # Register blueprints or routes
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    # Start the blockchain listener
    from .transaction_listener import start_blockchain_listener
    start_blockchain_listener(app)

    return app
