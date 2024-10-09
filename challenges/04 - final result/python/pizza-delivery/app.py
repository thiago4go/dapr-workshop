from flask import Flask, request
import json
import time
import logging
from dapr.clients import DaprClient
import random

DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'order'
DAPR_CRON_BINDING_NAME = 'deliverycron'
DAPR_STORE_NAME = 'pizzastatestore'
DAPR_PORT = 8003

logging.basicConfig(level=logging.INFO)


def deliver(order_data):
    # Simulate delivery time and events
    time.sleep(3)
    order_data['event'] = 'Delivery started'
    publish_event(order_data)

    time.sleep(3)
    order_data['event'] = 'Order picked up by driver'
    publish_event(order_data)

    time.sleep(5)
    order_data['event'] = 'En-route'
    publish_event(order_data)
    
    time.sleep(5)
    order_data['event'] = 'Nearby'
    publish_event(order_data)

    time.sleep(5)
    order_data['event'] = 'Delivered'
    publish_event(order_data)

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

app = Flask(__name__)

# ------------------- Application routes ------------------- #
@app.route('/deliver', methods=['POST'])
def startDelivery():
    order_data = request.json
    logging.info('Delivery started: %s', order_data['order_id'])

    wait = deliver(order_data)

    logging.info('Delivery completed: %s', order_data['order_id'])

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}

app.run(port=8003)