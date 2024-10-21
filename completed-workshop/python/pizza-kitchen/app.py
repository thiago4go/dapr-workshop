from flask import Flask, request
import json
import time
import logging
from dapr.clients import DaprClient
import random

DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'order'

DAPR_PORT = 6001

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

def start(order_data):
    # Generate a random prep time between 4 and 7 seconds
    prep_time = random.randint(4, 7)
    
    order_data['prep_time'] = prep_time
    order_data['event'] = 'Cooking'

    # Send cooking event to pubsub 
    publish_event(order_data)

    time.sleep(prep_time)

    return prep_time

def ready(order_data):
    order_data['event'] = 'Ready for delivery'

    # Send ready event to pubsub 
    publish_event(order_data)

    return order_data

# ------------------- Dapr pub/sub ------------------- #
def publish_event(order_data):
    with DaprClient() as client:
        # Publish an event/message using Dapr PubSub
        result = client.publish_event(
            pubsub_name=DAPR_PUBSUB_NAME,
            topic_name=DAPR_PUBSUB_TOPIC_NAME,
            data=json.dumps(order_data),
            data_content_type='application/json',
        )

# ------------------- Application routes ------------------- #
@app.route('/cook', methods=['POST'])
def startCooking():
    order_data = request.json
    logging.info('Cooking order: %s', order_data['order_id'])

    # Start cooking the order
    start(order_data)
    
    logging.info('Cooking done: %s', order_data['order_id'])

    # Order is ready for delivery
    ready(order_data)

    logging.info('Order %s is ready for delivery!', order_data['order_id'])

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}

app.run(port=6001)