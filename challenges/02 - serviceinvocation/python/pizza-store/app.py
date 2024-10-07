from flask import Flask, request
from flask_cors import CORS
from dapr.clients import DaprClient

import uuid
import logging
import json
import os
import requests

DAPR_STORE_NAME = 'pizzastatestore'
DAPR_PORT = 8001

logging.basicConfig(level=logging.WARN)

app = Flask(__name__)
CORS(app)

# ------------------- Dapr State Store ------------------- #

def save_order(order_id, order_data):
    with DaprClient() as client:
        # Save state 
        client.save_state(DAPR_STORE_NAME, order_id, str(order_data))
        logging.info('Saving Order %s with event %s', order_id, order_data['event'])

        return order_id
    
def get_order(order_id):
    with DaprClient() as client:
        # Get state
        result = client.get_state(DAPR_STORE_NAME, order_id)
        logging.info('Order result - %s', str(result.data))

        return result.data
    
def delete_order(order_id):
    with DaprClient() as client:
        # Delete state
        client.delete_state(DAPR_STORE_NAME, order_id)
        logging.info('Order deleted - %s', order_id)

        return order_id

# ------------------- Dapr Service Invocation ------------------- #
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

# ------------------- Dapr Pub/Sub ------------------- #

# ------------------- Application routes ------------------- #

# Cretae a new order
@app.route('/orders', methods=['POST'])
def createOrder():

    # Create a new order id
    order_id = str(uuid.uuid4())
    order_data = request.json

    order_data['order_id'] = order_id
    order_data['event'] = 'Sent to kitchen'

    # Save order to state store
    save_order(order_id, order_data)

    # Start cooking
    start_cook(order_data)

    return json.dumps({'orderId': order_id}), 200, {
        'ContentType': 'application/json'}

# Get order by id
@app.route('/orders/<order_id>', methods=['GET'])
def getOrder(order_id):
    if order_id:
        result = get_order(order_id)   
        result_str = result.decode('utf-8')     

        return json.dumps(result_str), 200, {
        'ContentType': 'application/json'}
    
    return json.dumps({'success': False, 'message': 'Missing order id'}), 404, {
        'ContentType': 'application/json'}

# Delete order by id
@app.route('/orders/<order_id>', methods=['DELETE'])
def deleteOrder(order_id):
    if order_id:
        delete_order(order_id)   

        return json.dumps({'orderId': order_id}), 200, {
        'ContentType': 'application/json'}
    
    return json.dumps({'success': False, 'message': 'Missing order id'}), 404, {
        'ContentType': 'application/json'}


app.run(port=8001)