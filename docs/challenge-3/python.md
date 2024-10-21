## Challenge 3 - Pub/Sub

### Overview

On our third challenge, our goal will be to update the state store with all the events from our order. For that, we will:

- Update our order with the following event states:

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
- Send all the events from our order to our new component: Pub/Sub.
- Update _pizza-kitchen_ and _pizza-store_ to publish events to our Pub/Sub using the Dapr SDK.
- Create a _subscription_ definition and with a route in our _pizza-store_ to save all the events to Redis.

To learn more about the Publish & subscribe building block, refer to the [Dapr docs](https://docs.dapr.io/developing-applications/building-blocks/pubsub/).

### Create the Pub/Sub component

Open the `/resources` folder and create a file called `pubsub.yaml`, add the following content:

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

Similar to our `statestore.yaml` file, this new definition creates a new component called _pizzapubsub_ of type _pubsub.redis_ pointing to our local Redis instance. Our apps will initialize this component to interact with it.

### Create the subscription definition

Still inside the `/resources` folder, create a new file called `subscription.yaml`. Add the following to it:

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

This file of kind subscription specifies that every time we get a new message in our Pub/Sub `pizzapubsub` in the topic `orders`, a route called `/events` will be triggered.

As a Dapr good practice, we are also introducing a _scope_ to this definition file. By setting `pizza-store` as our scope, we guarantee that this subscription rule will apply only to this service and will be ignored by others.

### Installing the dependencies

Navigate to `/pizza-delivery`. and run the command below to install the dependencies:

```bash
pip install -r requirements.txt
```

### Creating the service

Open `app.py`. Add the import statements below:

```python
from flask import Flask, request
from dapr.clients import DaprClient

import json
import time
import logging
```

Add the following constants, we will use them to connect to our Pub/Sub and topic:

```python
DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'order'
```

### Creating the app route

Leet's create our route `/deliver` that will tell the service to start a  delivery for our order. Below **# Application routes #** add the following:

```python
@app.route('/deliver', methods=['POST'])
def startDelivery():
    order_data = request.json
    logging.info('Delivery started: %s', order_data['order_id'])

    # Start delivery
    deliver(order_data)

    logging.info('Delivery completed: %s', order_data['order_id'])

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}
```

Create a new function called `deliver`. This will simply take our order and update it with multiple events, adding a small delay in between calls:

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

#### Publishing the event

Now let's publish! We will use the Dapr SDK to submit the event to our PubSub. Under **Dapr pub/sub** add:

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

Our Delivery service is completed. Let's update _pizza-kitchen_ and _pizza-store_. now.

#### Sending the Kitchen events

Open `python/pizza-kithen` and add the following lines below the import statements:

```python
DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'order'
```

Under **Dapr pub/sub**, add the following lines to send our event to the pub/sub:

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

Now, Update the `start(order_data):` and the `ready(order_data):` functions by adding a call to our `publish_event`:

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

#### Starting a delivery service

Going back to the _pizza-store_ service, let's update the import statements:

```python
from flask import Flask, request
from flask_cors import CORS
from dapr.clients import DaprClient

import uuid
import logging
import json
import os
import requests
```

Add the folliowing contants referencing our pub/sub and the topic we will publish to:

```python
DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'order'
```

Now, let's add a new service invocation function under **Dapr Service Invocation**. This is the same process from the second challenge, but now we are sending the order to our _pizza-delivery_ service by posting the order to the `/deliver` endpoint. This starts the order delivery:

```python
def start_delivery(order_data):
    base_url = os.getenv('BASE_URL', 'http://localhost') + ':' + os.getenv('DAPR_HTTP_PORT', '3501')

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
```

#### Publishing and subscribing to events

First, let's change our `createOrder():` function to publish an event to our pub/sub. Replace the line below:

```python
# Save order to state store
save_order(order_id, order_data)

# Start cooking
start_cook(order_data)
```

By:

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

With this, we are now replacing direct calls to `save_oder` and `start_cook`  with a `publish_event` process. This will send the events to Redis(our Pub/Sub component). In the next step we will subscribe to these events and save them to our state store.

#### Subscribing to events

Let's create the route `/events`. This route was previously specified in our `subscription.yaml` file as the endpoint that will ve triggered once a new event is published to the `orders` topic.

Under **Dapr Pub/Sub** include:

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

    return json.dumps({'success': "True"}), 200, {
        'ContentType': 'application/json'}
```

The code above picks up the order from the topic, checks for the `order_id` and the `event`. The order with the new event is saved to the state store and, based on the type of event, we either send the event to the kitchen or to the delivery service.


#### Running the application

We now need to run all three applications. If the _pizza-store_ and the _pizza-kitchen_ services are still running, press **CTRL+C** in each terminal window to stop them. In your terminal, navigate to the folder where the _pizza-store_ `app.py` is located and run the command below:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3501 --resources-path ../../resources  -- python3 app.py
```

Open a new terminal window and mode to the _pizza-kitchen_ folder. Run the command below:

```bash
dapr run --app-id pizza-kitchen --app-protocol http --app-port 8002 --dapr-http-port 3502  --resources-path ../../resources -- python3 app.py
```

Finally, opena  third terminal window and navigate to the _pizza-delivery_ service. Run the command below:

```bash
dapr run --app-id pizza-delivery --app-protocol http --app-port 8003 --dapr-http-port 3503 --resources-path ../../resources  -- python3 app.py
```

> [!IMPORTANT]
> If you are using Consul as a naming resolution service, add `--config ../resources/config/config.yaml` before `-- python3 app.py` on your Dapr run command.

Check for the logs for all three services, you should now see the pubsub component loaded:

```bash
INFO[0000] Component loaded: pizzapubsub (pubsub.redis/v1)  app_id=pizza-store instance=diagrid.local scope=dapr.runtime.processor type=log ver=1.14.4
```

#### Testing the service

Open a fourth terminal window and create a new order:

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:8001/orders
```

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

## Running the front-end application

Now that you've completed all the challenges, let's order a pizza using the UI.

With all services still running, navigate to `/pizza-frontend`, open a new terminal, and run:

```bash
python3 -m http.server 8080
```

Open a browser window and navigate to `localhost:8080`, fill-out your order on the right-hand side and press `Place Order`. All the events will pop-up at the bottom for you.

![front-end](/imgs/front-end.png)

## Dapr multi-app run

Instead of opening multiple terminals to run the services, we can take advantage of a great Dapr feature: [multi-app run](https://docs.dapr.io/developing-applications/local-development/multi-app-dapr-run/multi-app-overview/).

Inside the `/python` folder, create a new file called `dapr.yaml`. Add the following content to it:

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

## Congratulations

Congratulations in completing all of the three challenges. Stop by our booth to show all challenges completed and get some swag for your hard work!

You have now scratched the surface of what Dapr can do. It's highly recommended navigating to the [Dapr docs](https://docs.dapr.io/) and learning more about it.
