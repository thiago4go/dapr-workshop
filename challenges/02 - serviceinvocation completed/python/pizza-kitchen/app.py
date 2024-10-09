from flask import Flask, request
import json
import time
import logging
from dapr.clients import DaprClient
import random

DAPR_PORT = 8002

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

def start(order_data):
    # Generate a random prep time between 4 and 7 seconds
    prep_time = random.randint(4, 7)
    
    # Updating order data with prep time and setting a new event to it: Cooking
    order_data['prep_time'] = prep_time
    order_data['event'] = 'Cooking'

    logging.info('Order %s updated with event: %s', order_data['order_id'], order_data['event'])

    return order_data

def ready(order_data):
    # Setting a new event to order data: Ready for delivery
    order_data['event'] = 'Ready for delivery'

    return order_data

# ------------------- Dapr pub/sub ------------------- #


# ------------------- Application routes ------------------- #
@app.route('/cook', methods=['POST'])
def startCooking():
    order_data = request.json
    logging.info('Cooking order: %s', order_data['order_id'])

    # Start cooking the order
    order_data = start(order_data)
    
    # Waiting for order to be completed
    time.sleep(order_data['prep_time'])

    # Order is ready for delivery
    ready(order_data)
    logging.info('Order %s is ready for delivery!', order_data['order_id'])

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}

app.run(port=8002)