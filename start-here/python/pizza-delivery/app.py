from flask import Flask, request
import json
import time
import logging
from dapr.clients import DaprClient
import random

DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'order'
DAPR_PORT = 8002

logging.basicConfig(level=logging.INFO)

def deliver(order_data):
    # Generate a random prep time between 5 and 15 seconds
    prep_time = random.randint(5, 15)
    order_data['prep_time'] = prep_time

    order_data['event'] = 'Cooking'

    # Send cooking event to pubsub 
    publish_event(order_data)

    return prep_time

def ready(order_data):
    order_data['event'] = 'Ready'

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
        logging.info('Published order to pubsub: %s', json.dumps(order_data))


app = Flask(__name__)

# ------------------- Application routes ------------------- #
@app.route('/cook', methods=['POST'])
def startCooking():
    order_data = request.json
    print('Cooking order: %s', order_data['order_id'])

    wait = start(order_data)
    time.sleep(wait)

    print('Cooking done')
    ready(order_data)

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}

app.run(port=8002)