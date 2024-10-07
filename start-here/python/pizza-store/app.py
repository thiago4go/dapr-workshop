from flask import Flask, request, jsonify
from flask_cors import CORS
from cloudevents.http import from_http
from dapr.clients import DaprClient

import uuid
import os
import time
import logging
import json
import requests


DAPR_STORE_NAME = 'pizzastatestore'
DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'order'
DAPR_PORT = 8001

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

def save_order(order_id, order_data):

    with DaprClient() as client:

        # Save state into the state store
        client.save_state(DAPR_STORE_NAME, order_id, str(order_data))
        logging.info('Saving Order %s with event %s', order_id, order_data['event'])

        return order_id
    
def get_order(order_id):

    with DaprClient() as client:

        # Get state into the state store
        result = client.get_state(DAPR_STORE_NAME, order_id)

        return result.data

# ------------------- Dapr service invocation ------------------- #

def start_cook(order_data):
    base_url = os.getenv('BASE_URL', 'http://localhost') + ':' + os.getenv(
                    'DAPR_HTTP_PORT', '3500')
    # Adding app id as part of the header
    headers = {'dapr-app-id': 'pizza-kitchen', 'content-type': 'application/json'}

    url = '%s/cook' % (base_url)
    print('url: ' + url, flush=True)

    # Invoking a service
    result = requests.post(
        url=url,
        data=json.dumps(order_data),
        headers=headers
    )
    print('result: ' + str(result), flush=True)

    time.sleep(1)

def start_delivery(order_data):
    base_url = os.getenv('BASE_URL', 'http://localhost') + ':' + os.getenv(
                    'DAPR_HTTP_PORT', '3500')
    # Adding app id as part of the header
    headers = {'dapr-app-id': 'pizza-delivery', 'content-type': 'application/json'}

    url = '%s/deliver' % (base_url)
    print('url: ' + url, flush=True)

    # Invoking a service
    result = requests.post(
        url=url,
        data=json.dumps(order_data),
        headers=headers
    )
    print('result: ' + str(result), flush=True)

    time.sleep(1)

# ------------------- Dapr pub/sub ------------------- #

# Dapr subscription in /dapr/subscribe sets up this route
@app.route('/events', methods=['POST'])
def orders_subscriber():
    event = from_http(request.headers, request.get_data())
    order_id = event.data['order_id']
    event_type = event.data['event']

    logging.info('%s - %s', order_id, event_type)

    save_order(event.data['order_id'], event.data)

    # check if the event is ready for delivery
    if event_type == 'Ready for delivery':
        start_delivery(event.data)

    response = jsonify({'success': True})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('ContentType', 'application/json')
    return response


# ------------------- Application routes ------------------- #

@app.route('/orders', methods=['POST'])
def createOrder():

    # Create a new order id
    order_id = str(uuid.uuid4())
    order_data = request.json

    order_data['order_id'] = order_id
    order_data['event'] = 'Sent to kitchen'

    # Save order to state store
    save_order(order_id, order_data)

    # Send order to kitchen
    start_cook(order_data)

    return json.dumps({'orderId': order_id}), 200, {
        'ContentType': 'application/json'}

@app.route('/orders/<order_id>', methods=['GET'])
def getOrder(order_id):
    if order_id:
        result = get_order(order_id)   
        result_str = result.decode('utf-8')     

        return json.dumps(result_str), 200, {
        'ContentType': 'application/json'}
    
    return json.dumps({'success': False, 'message': 'Missing order id'}), 404, {
        'ContentType': 'application/json'}


app.run(port=8001)