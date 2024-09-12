from flask import Flask, request, jsonify
from flask_mqtt import Mqtt

app = Flask(__name__)

# MQTT Configuration
app.config['MQTT_BROKER_URL'] = 'v012a1b1.ala.us-east-1.emqxsl.com'
app.config['MQTT_BROKER_PORT'] = 8883  # Port for TLS
app.config['MQTT_USERNAME'] = 'backend'  # Set username if required
app.config['MQTT_PASSWORD'] = 'backend'  # Set password if required
app.config['MQTT_KEEPALIVE'] = 5  # KeepAlive time in seconds
app.config['MQTT_TLS_ENABLED'] = True  # Enable TLS
app.config['MQTT_TLS_CA_CERTS'] = 'ca_certificate.crt'  # Path to the CA certificate
app.config['MQTT_TLS_VERSION'] = 2
# Initialize Flask-MQTT client
mqtt_client = Mqtt(app)

# Topic to subscribe
topic = 'emqx/esp8266'


# Handle MQTT connection event
@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Connected to MQTT Broker successfully')
        # Subscribe to all topics
        mqtt_client.subscribe(topic)  
    else:
        print(f'Failed to connect to MQTT Broker. Connection code: {rc}')


# Handle incoming MQTT messages
@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, message):
    data = {
        'topic': message.topic,
        'payload': message.payload.decode()  # Decode the message payload
    }
    print(f"Received message on topic: {data['topic']} with payload: {data['payload']}")


# Route to publish MQTT messages
@app.route('/publish', methods=['POST'])
def publish_message():
    request_data = request.get_json()
    
    if not request_data or 'topic' not in request_data or 'msg' not in request_data:
        return jsonify({'error': 'Invalid request'}), 400
    
    # Publish the message to the given topic
    publish_result = mqtt_client.publish(request_data['topic'], request_data['msg'])
    
    if publish_result[0] == 0:
        return jsonify({'message': 'Message published successfully'}), 200
    else:
        return jsonify({'error': 'Failed to publish message'}), 500


# Run the Flask app
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
