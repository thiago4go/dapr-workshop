# Challenge 4 - Workflow

## Overview

In the third challenge, the goal is to update the state store with all the events from pizza order. For that, you will:

- Update the order with the following event states:

```text
Sent to kitchen
Cooking
Ready for delivery
Order picked up by driver
Delivery started
En-route
Nearby
Delivered
```

- Create a new service called _pizza-delivery_ which is responsible for... delivering the pizza :).
- Send the events containing the state of the order to the new Dapr component, a pub/sub message broker.
- Update _pizza-kitchen_ and _pizza-store_ to publish events to the Pub/Sub using the Dapr SDK.
- Create a _subscription_ definition route in the _pizza-store_ to save all the state events to the state store.

<img src="../../imgs/challenge-3.png" width=75%>

To learn more about the Publish & Subscribe building block, refer to the [Dapr docs](https://docs.dapr.io/developing-applications/building-blocks/pubsub/).

## Create the Pub/Sub component

Open the `/resources` folder and create a file called `pubsub.yaml`. Add the following content:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pizzapubsub
spec:
  type: pubsub.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
  - name: redisPassword
    value: ""
```

Similar to our `statestore.yaml` file, this new definition creates a Dapr component called _pizzapubsub_ of type _pubsub.redis_ pointing to the local Redis instance. Each app will initialize this component to interact with it.

## Create a subscription

Still inside the `/resources` folder, create a new file called `subscription.yaml`. Add the following content to it:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: pizza-store-subscription
spec:
  topic: order
  route: /events
  pubsubname: pizzapubsub
scopes: 
- pizza-store  
```

This file of kind `Subscription` specifies that every time the Pub/Sub `pizzapubsub` component receives a message in the `orders` topic, this message will be sent to a route called `/events` on the scoped `pizza-store` service. By setting `pizza-store` as the only scope, we guarantee that this subscription rule will only apply to this service and will be ignored by others. Finally, the `/events` endpoint needs to be created in the `pizza-store` service in order to receive the events.

## Install the dependencies

Open a new terminal window and create another virtual enviroment:

```bash
python -m venv env
source env/bin/activate
```

Navigate to the `/pizza-delivery` folder and run this command to install the dependencies:

```bash
pip install -r requirements.txt
```

## Create the service

Open `app.py`. Add the import statements below:

```python
from flask import Flask, request, jsonify
from dapr.clients import DaprClient

import json
import time
import logging
```

Add the following constants, they will be used to connect to our Pub/Sub and topic:

```python
DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'order'
```

## Create the app route

Create the route `/deliver` that will instruct the service to start a  delivery for the pizza order.  Below **# Application routes #** add the following code:

```python
@app.route('/deliver', methods=['POST'])
def startDelivery():
    order_data = request.json
    logging.info('Delivery started: %s', order_data['order_id'])

    # Start delivery
    deliver(order_data)

    logging.info('Delivery completed: %s', order_data['order_id'])

    return jsonify({'success': True})
```

Under **# Dapr Pub/Sub #** create a new function called `deliver`. This will take the order and update it with multiple events, adding a small delay in between calls:

```python
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
```

## Publish the event

Now its time to publish the events using Dapr! Under **# Dapr pub/sub #** add:

```python
def publish_event(order_data):
    with DaprClient() as client:
        # Publish an event/message using Dapr PubSub
        result = client.publish_event(
            pubsub_name=DAPR_PUBSUB_NAME,
            topic_name=DAPR_PUBSUB_TOPIC_NAME,
            data=json.dumps(order_data),
            data_content_type='application/json',
        )
```

The code above uses the Dapr SDK to publish an event to the PubSub infrastructure (Redis). That event is the `order` in json format.

The _delivery-service_ is now completed. Update _pizza-kitchen_ and _pizza-store_ now in the next sections of this challenge.

## Send the Kitchen events

Open the `python/pizza-kitchen` folder and add the following lines to the `app.py` file below the import statements:

```python
DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'order'
```

Under **# Dapr pub/sub #**, add the following lines to send the order event to the message broker:

```python
def publish_event(order_data):
    with DaprClient() as client:
        # Publish an event/message using Dapr PubSub
        result = client.publish_event(
            pubsub_name=DAPR_PUBSUB_NAME,
            topic_name=DAPR_PUBSUB_TOPIC_NAME,
            data=json.dumps(order_data),
            data_content_type='application/json',
        )
```

Now, update the `start(order_data):` and the `ready(order_data):` functions by adding a call to the `publish_event` function:

```python
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
```

## Call the delivery service

Going back to the _pizza-store_ service, update the imports to be:

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
from cloudevents.http import from_http
from dapr.clients import DaprClient

import requests
import uuid
import time
import logging
import json
```

Add the folliowing contants referencing the pub/sub and the topic to publish to:

```python
DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'order'
```

Add a new service invocation function under **# Dapr Service Invocation #**. This is the same process from the second challenge, but now you are sending the order to the _pizza-delivery_ service by posting the order to the `/deliver` endpoint. This starts the order delivery:

```python
def start_delivery(order_data):
    app_id = 'pizza-delivery'
    headers = {'dapr-app-id': app_id, 'content-type': 'application/json'}
    
    base_url = 'http://localhost'
    method = 'deliver'
    dapr_http_port = 3501
    target_url = '%s:%s/%s' % (base_url, dapr_http_port, method)

    response = requests.post(
        url=target_url,
        data=json.dumps(order_data),
        headers=headers
    )
    print('result: ' + response.text, flush=True)
    time.sleep(1)
```

## Publish events

First, change the `createOrder():` function to publish an event to the pub/sub message broker. Replace the lines below:

```python
# Save order to state store
save_order(order_id, order_data)

# Start cooking
start_cook(order_data)
```

With:

```python
# Publish an event/message using Dapr PubSub
with DaprClient() as client:
    client.publish_event(
        pubsub_name=DAPR_PUBSUB_NAME,
        topic_name=DAPR_PUBSUB_TOPIC_NAME,
        data=json.dumps(order_data),
        data_content_type='application/json',
    )
```

With this, you are now replacing direct calls to `save_order` and `start_cook`  with a `publish_event` process. This will send the events to the Redis Pub/Sub component. In the next step you will subscribe to these events and save them to the state store.

## Subscribe to events

Create the route `/events`. This route was previously specified in our `subscription.yaml` file as the endpoint that will be triggered once a new event is published to the `orders` topic.

Under **# Dapr Pub/Sub #** include:

```python
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
```

The code above picks up the order from the topic, checks for the `order_id` and the `event_type`. The order with the new event is saved to the state store and, based on the type of event, it is either sent to the _pizza-kitchen_ or to the _pizza-delivery_ service.

#### Run the application

It's time to run all three applications. If the _pizza-store_ and the _pizza-kitchen_ services are still running, press **CTRL+C** in each terminal window to stop them.

In the terminal for _pizza-store_ run:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3501 --resources-path ../resources  -- python3 app.py
```

In the terminal for _pizza-kitchen_ run:

```bash
dapr run --app-id pizza-kitchen --app-protocol http --app-port 8002 --dapr-http-port 3502  --resources-path ../resources -- python3 app.py
```

In the terminal for _pizza-delivery_ run:

```bash
dapr run --app-id pizza-delivery --app-protocol http --app-port 8003 --dapr-http-port 3503 --resources-path ../resources  -- python3 app.py
```

> [!IMPORTANT]
> If you are using Consul as a naming resolution service, add `--config ../resources/config/config.yaml` before `-- python3 app.py` on your Dapr run command.

Check for the logs for all three services, you should now see the pubsub component loaded:

```bash
INFO[0000] Component loaded: pizzapubsub (pubsub.redis/v1)  app_id=pizza-store instance=diagrid.local scope=dapr.runtime.processor type=log ver=1.14.4
```

## Test the service

### Use VS Code REST Client

Open `PizzaStore.rest` and create a new order, similar to what was done previous challenges.

Navigate to the _pizza-store_ terminal, you should see the following logs pop up with all the events being updated:

```zsh
== APP == INFO:root:Subscription triggered for order: 93a1072c-956d-4bbf-926f-ace066a83ec2. Event: Sent to kitchen
== APP == INFO:root:Saving Order 93a1072c-956d-4bbf-926f-ace066a83ec2 with event Sent to kitchen
== APP == INFO:root:Subscription triggered for order: 93a1072c-956d-4bbf-926f-ace066a83ec2. Event: Cooking
== APP == INFO:root:Saving Order 93a1072c-956d-4bbf-926f-ace066a83ec2 with event Cooking
== APP == INFO:root:Subscription triggered for order: 93a1072c-956d-4bbf-926f-ace066a83ec2. Event: Ready for delivery
== APP == INFO:root:Saving Order 93a1072c-956d-4bbf-926f-ace066a83ec2 with event Ready for delivery
== APP == INFO:root:Subscription triggered for order: 93a1072c-956d-4bbf-926f-ace066a83ec2. Event: Delivery started
== APP == INFO:root:Saving Order 93a1072c-956d-4bbf-926f-ace066a83ec2 with event Delivery started
== APP == INFO:root:Subscription triggered for order: 93a1072c-956d-4bbf-926f-ace066a83ec2. Event: Order picked up by driver
== APP == INFO:root:Saving Order 93a1072c-956d-4bbf-926f-ace066a83ec2 with event Order picked up by driver
== APP == INFO:root:Subscription triggered for order: 93a1072c-956d-4bbf-926f-ace066a83ec2. Event: En-route
== APP == INFO:root:Saving Order 93a1072c-956d-4bbf-926f-ace066a83ec2 with event En-route
== APP == INFO:root:Subscription triggered for order: 93a1072c-956d-4bbf-926f-ace066a83ec2. Event: Nearby
== APP == INFO:root:Saving Order 93a1072c-956d-4bbf-926f-ace066a83ec2 with event Nearby
== APP == INFO:root:Subscription triggered for order: 93a1072c-956d-4bbf-926f-ace066a83ec2. Event: Delivered
== APP == INFO:root:Saving Order 93a1072c-956d-4bbf-926f-ace066a83ec2 with event Delivered
```

### Use _cURL_

Open a fourth terminal window and create a new order:

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:8001/orders
```

## Run the front-end application

Now that you've completed all the challenges, its time to order a pizza using the UI.

With all services still running, navigate to `/pizza-frontend`, open a new terminal, and run:

```bash
python3 -m http.server 8080
```

Open a browser window and navigate to `localhost:8080`, fill-out your order on the right-hand side and click `Place Order`. All the events will pop-up at the bottom for you.

![front-end](/imgs/front-end.png)

## Dapr multi-app run

Instead of opening multiple terminals to run the services, you can take advantage of a great Dapr CLI feature: [multi-app run](https://docs.dapr.io/developing-applications/local-development/multi-app-dapr-run/multi-app-overview/). This enables you run all three services with just one command!

In the parent folder, create a new file called `dapr.yaml`. Add the following content to it:

```yaml
version: 1
common:
  resourcesPath: ../resources
  # Uncomment the following line if you are running Consul for service naming resolution
  # configFilePath: ./resources/config/config.yaml
apps:
  - appDirPath: ./pizza-store/
    appID: pizza-store
    daprHTTPPort: 3501
    appPort: 8001
    command: ["python3", "app.py"]
  - appDirPath: ./pizza-kitchen/
    appID: pizza-kitchen
    appPort: 8002
    daprHTTPPort: 3502
    command: ["python3", "app.py"]
  - appDirPath: ./pizza-delivery/
    appID: pizza-delivery
    appPort: 8003
    daprHTTPPort: 3503
    command: ["python3", "app.py"]
```

Stop the services, if they are running, and enter the following command in the terminal:

```bash
dapr run -f .
```

All three services will run at the same time and log events at the same terminal window.

## Next steps

Congratulations, you have completed all the challenges and you can claim your [reward](../completion.md)!
