from flask import Flask, request, jsonify
from flask_cors import CORS
from cloudevents.http import from_http
from dapr.clients import DaprClient

import uuid
import time
import logging
import json

DAPR_PORT = 8001
DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'order'

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

DAPR_STORE_NAME = 'pizzastatestore'

# ------------------- Dapr State Store ------------------- #

def save_order(order_id, order_data):
    with DaprClient() as client:
        # Save state 
        client.save_state(DAPR_STORE_NAME, order_id, json.dumps(order_data))
        logging.info('Saving Order %s with event %s', order_id, order_data['event'])

        return order_id

def get_order(order_id):
    with DaprClient() as client:
        # Get state
        result = client.get_state(DAPR_STORE_NAME, order_id)
        logging.info('Order result - %s', str(result.data))

        return json.loads(result.data)
    
def delete_order(order_id):
    with DaprClient() as client:
        # Delete state
        client.delete_state(DAPR_STORE_NAME, order_id)
        logging.info('Order deleted - %s', order_id)

        return order_id

# ------------------- Dapr Service Invocation ------------------- #

def start_cook(order_data):
    with DaprClient() as client:
        response = client.invoke_method(
            'pizza-kitchen',
            'cook',
            http_verb='POST',
            data=json.dumps(order_data),
        )
        print('result: ' + response.text(), flush=True)

def start_delivery(order_data):
    with DaprClient() as client:
        response = client.invoke_method(
            'pizza-delivery',
            'deliver',
            http_verb='POST',
            data=json.dumps(order_data),
        )
        print('result: ' + response.text(), flush=True)
        time.sleep(1)

# ------------------- Dapr Pub/Sub ------------------- #

# Endpoint triggered when a new event is published to the topic 'order'
@app.route('/events', methods=['POST'])
def orders_subscriber():
    # retrieves the published order
    order = from_http(request.headers, request.get_data())

    # retrieves the order id and event type
    order_id = order.data['order_id']
    event_type = order.data['event']

    logging.info('%s - %s', order_id, event_type)

    # saves the order to the state store
    save_order(order.data['order_id'], order.data)

    # check if the event is sent to kitchen
    if event_type == 'Sent to kitchen':
        # Send order to kitchen
        time.sleep(4)
        start_cook(order.data)

    # check if the event is ready for delivery
    if event_type == 'Ready for delivery':
        # Starts a delivery
        start_delivery(order.data)

    return jsonify({'success': "True"})


# ------------------- Application routes ------------------- #

# Create a new order
@app.route('/orders', methods=['POST'])
def createOrder():

    # Create a new order id
    order_id = str(uuid.uuid4())
    order_data = request.json

    # add order id to order data and set a new event to it
    order_data['order_id'] = order_id
    order_data['event'] = 'Sent to kitchen'

    # Publish an event/message using Dapr PubSub
    with DaprClient() as client:
        client.publish_event(
            pubsub_name=DAPR_PUBSUB_NAME,
            topic_name=DAPR_PUBSUB_TOPIC_NAME,
            data=json.dumps(order_data),
            data_content_type='application/json',
        )

    return jsonify({'orderId': order_id})

# Get order by id
@app.route('/orders/<order_id>', methods=['GET'])
def getOrder(order_id):
    if order_id:
        result = get_order(order_id)

        return jsonify(result)
    
    return jsonify({'success': False, 'message': 'Missing order id'}), 404

# Delete order by id
@app.route('/orders/<order_id>', methods=['DELETE'])
def deleteOrder(order_id):
    if order_id:
        delete_order(order_id)   

        return jsonify({'orderId': order_id})
    
    return jsonify({'success': False, 'message': 'Missing order id'}), 404

app.run(port=DAPR_PORT)
