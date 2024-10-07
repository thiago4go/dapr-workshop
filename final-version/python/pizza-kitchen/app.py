from flask import Flask, request
import json
import time
import logging
from dapr.clients import DaprClient
import random

DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'order'
DAPR_PORT = 8002

# logging.basicConfig(level=logging.INFO)

def start(order_data):
    # Generate a random prep time between 4 and 7 seconds
    prep_time = random.randint(4, 7)
    
    order_data['prep_time'] = prep_time
    order_data['event'] = 'Cooking'

    time.sleep(prep_time)

    # Send cooking event to pubsub 
    publish_event(order_data)
    

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
        #logging.info('Published order to pubsub: %s', json.dumps(order_data))

app = Flask(__name__)

# ------------------- Application routes ------------------- #
@app.route('/cook', methods=['POST'])
def startCooking():
    order_data = request.json
    logging.info('Cooking order: %s', order_data['order_id'])

    start(order_data)
    
    logging.info('Cooking done: %s', order_data['order_id'])
    ready(order_data)

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}

app.run(port=8002)