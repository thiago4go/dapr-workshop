# Python

## Clone the repository and initialize the environment

On your terminal, run:

```bash
git clone https://github.com/diagrid-labs/dapr-workshop.git
cd dapr-worksop
```

Navigate to the starting point:

```bash
cd start-here
```

Install vevn:

```bash
pip install virtualenv
```

Initialize the virtual environment:

```bash
python -m venv env
source env/bin/activate
```

## Challenge 1 - State Store

### Overview

On our first challenge, we will:

- Create our first Dapr application: _pizza-store_.
- Configure a State Store component for our local Redis instance to save, get, and delete an order.
- Run our app locally using `dapr run`.

To learn more about the State Management Building block, refer to the [Dapr docs](https://docs.dapr.io/developing-applications/building-blocks/state-management/state-management-overview/).

### Configuring the state store

Navigate to the `/resources` folder and create a new file called `statestore.yaml`. Add the content below to the file:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pizzastatestore
spec:
  type: state.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
  - name: redisPassword
    value: ""
```

This is a component definition file named `pizzastatestore`. In the _spec_ definition, note that the type of the component is `state_redis` and the metadata contains host and password information for our Redis instance that was deployed as a container during Dapr's initialization. process.

### Installing the dependencies

Now navigate to `python/pizza-store`. This folder contains the `app.py` file which contains our application. Before start coding, let's install our dependencies.

Let's start by creating a new file called `requirements.txt`. This file will hold our dependencies. Add the content below to it:

```text
Flask
flask-cors
dapr
uvicorn
typing-extensions
```

Run the command below to install the dependencies:

```bash
pip install -r pizza-store/requirements.txt
```

### Creating the service

Open `app.py`. Notice the two import lines, let's add a couple more libraries there:

```python
from flask import Flask, request
from flask_cors import CORS
from dapr.clients import DaprClient

import uuid
import logging
import json
```

We are now importing _DaprClient_ from _dapr.clients_. That's what we will use to manage the state in our Redis instance.

#### Managing state

Let's create three new functions: `save_order`, `get_order`, and `delete_order`.

Start by creating a const:

```python
DAPR_STORE_NAME = 'pizzastatestore'
```

The name given to this const is the same name provided to our resources yaml file, created in the step above.

Under **# Dapr State Store #** add the following lines of code:

```python
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
```

1. `client.save_state(DAPR_STORE_NAME, order_id, str(order_data))` saves the state the Redis using a key/value pair. We need to pass the state store name, the order id as a **key**, and a json representation of the order as a **value**.

2. `result = client.get_state(DAPR_STORE_NAME, order_id)` retrieves the state from the store. It requires a key and the state store name.

3. `client.delete_state(DAPR_STORE_NAME, order_id)` deletes the state from the store. It also requires a key and the state store name.

### Creating the app routes

Before testing our application, we need to create routes so we are able to manage our state store from the frontend and by calling the REST APIs directly. Add three new routes below **# Application routes #**:

```python
# Create a new order
@app.route('/orders', methods=['POST'])
def createOrder():

    # Create a new order id
    order_id = str(uuid.uuid4())
    order_data = request.json

    # add order id to order data and set a new event to it
    order_data['order_id'] = order_id
    order_data['event'] = 'Sent to kitchen'

    # Save order to state store
    save_order(order_id, order_data)

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
```

To save the event we generate a new order UUID and set a new event: _Sent to Kitchen_. We will use these events during the next challenges.

#### Running the application

Now, open a terminal and navigate to the folder where `app.py` is located. Run the following command:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3500 --resources-path ../../resources  -- python3 app.py
```

This command sets:
    - an app-id `pizza-store` to our application
    - the app-protocol `http`
    - an  app-port `8001` for external communication and and http-port `3500` for sidecar communication
    - the resources-path, where our state store component definition file is locatated. This will guarantee that our component is loaded once the app initializes.

Look for the log entry below to guarantee that the state store was loaded successfully:

```bash
INFO[0000] Component loaded: pizzastatestore (state.redis/v1)  app_id=pizza-store instance=diagrid.local scope=dapr.runtime.processor type=log ver=1.14.4
```

#### Testing the service

Run the command below to create a new order.

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:8001/orders
```

If you downloaded Redis Insight, you can visualize the new entry there:

![redis-insight](/imgs/redis-insight.png)


Take note of the new order-id generated and run the following command to get the newly created order:

```bash
curl -H 'Content-Type: application/json' \
    -X GET \
    http://localhost:8001/orders/<order-id>
```

Finally, to delete the order:
```bash
curl -H 'Content-Type: application/json' \
    -X DELETE \
    http://localhost:8001/orders/<order-id>
```

## Challenge 2 - Service Invocation

### Overview

On our second challenge, we will send the order created in the previous step to the kitchen! For that, we will:

- Create a new service called _pizza-kitchen_ with a `/cook` endpoint.
- Update _pizza-store_ to invoke the `/cook` endpoint with the Service Invocation building block.

To learn more about the Service Invocation building block, refer to the [Dapr docs](https://docs.dapr.io/developing-applications/building-blocks/service-invocation/).

### Installing the dependencies

Navigate to `python/pizza-kitchen`. Let's install our dependencies

Open the file called `requirements.txt`. Add the content below to it:

```text
Flask
dapr
cloudevents
uvicorn
typing-extensions
```

Run the command below to install the dependencies:

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
import random
```

### Creating the app route

Leet's create our route that will tell the kitchen to start cooking the pizza `/cook`. Below **# Application routes #** add the following:

```python
@app.route('/cook', methods=['POST'])
def startCooking():
    order_data = request.json
    logging.info('Cooking order: %s', order_data['order_id'])

    # Start cooking
    start(order_data)
    
    logging.info('Cooking done: %s', order_data['order_id'])
    
    # Set the order as ready
    ready(order_data)

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}
```

This route is fairly simple. It is a POST request with the `order` content created in the last challenge. We will start the order and, after it is cooked, we will say it is ready.

Add two helper functions to modify the order to _Cooking_ and to _Ready for delivery_.

```python
def start(order_data):
    # Generate a random prep time between 4 and 7 seconds
    prep_time = random.randint(4, 7)
    
    order_data['prep_time'] = prep_time
    order_data['event'] = 'Cooking'

    time.sleep(prep_time)

    return prep_time

def ready(order_data):
    order_data['event'] = 'Ready for delivery'

    return order_data
```

#### Calling the app route

Let's go back to the _pizza-store_ service. We will create a Service Invocation action to call the `/cook` endpoint from our _pizza-kitchen_ service.

First, update the `createOrder()` function, add the following line after the `save_order((order_id, order_data))` invocation:

```python
 # Start cooking
start_cook(order_data)
```

Now, under **# Dapr Service Invocation #**, add the code below:

```python
def start_cook(order_data):
    # Set base url
    base_url = os.getenv('BASE_URL', 'http://localhost') + ':' + os.getenv(
                    'DAPR_HTTP_PORT', '3500')
    
    # Adding pizza-kitchen's app id as part of the header
    headers = {'dapr-app-id': 'pizza-kitchen', 'content-type': 'application/json'}

    # Adding the endpoint /cook to the base url
    url = '%s/cook' % (base_url)

    # Invoking the service
    result = requests.post(
        url=url,
        data=json.dumps(order_data),
        headers=headers
    )
    print('result: ' + str(result), flush=True)
```

Let's break down the code above.

1. First we are setting the base URL:

```python
base_url = os.getenv('BASE_URL', 'http://localhost') + ':' + os.getenv('DAPR_HTTP_PORT', '3500')
```

Notice that the code above calls a URL with the host `localhost` with the port `3500`. This is not calling the _pizza-kitchen_ service directly, but the sidecar of the _pizza-store_ service. The responsiblity of making the service invocation is passed to the sidecar, as the picture below illustrates:

TODO: ADD PICTURE

2. Then, we add the headers and the endpoint:

```python
# Adding pizza-kitchen's app id as part of the header
headers = {'dapr-app-id': 'pizza-kitchen', 'content-type': 'application/json'}

# Adding the endpoint /cook to the base url
url = '%s/cook' % (base_url)
```

The code above creates the header that is going to be attached to our request. The most important piece is the `'dapr-app-id': 'pizza-kitchen'`. By adding this to the header and including the route `/cook` to the end of the base URL, the _pizza-store_ sidecar knows exactly the service and route that it needs to invoke.

With this, services only need to communicate to sidecars through localhost and the sidecar handles the discovery capabilities.

3. Finally, we send the request:

```python
# Invoking the service
result = requests.post(
    url=url,
    data=json.dumps(order_data),
    headers=headers
)
print('result: ' + str(result), flush=True)
```

#### Running the application

We now need to run both applications. If the _pizza-store_ service is still running, press **CTRL+C** to stop it. In your terminal, navigate to the folder where the _pizza-store_ `app.py` is located and run the command below:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3500 --resources-path ../../resources  -- python3 app.py
```

Open a new terminal window and mode to the _pizza-kitchen_ folder. Run the command below:

```bash
dapr run --app-id pizza-kitchen --app-protocol http --app-port 8002 --dapr-http-port 3502  -- python3 app.py
```

#### Testing the service

Open a third terminal window and create a new order:

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:8001/orders
```

Navigate to the _pizza-kitchen_ terminal, you should see the following logs pop up:

```zsh
== APP == INFO:root:Cooking order: f75d9c94-155c-40ce-80c1-94296d2b51e9
== APP == INFO:root:Order f75d9c94-155c-40ce-80c1-94296d2b51e9 updated with event: Cooking
== APP == INFO:root:Order f75d9c94-155c-40ce-80c1-94296d2b51e9 is ready for delivery!
== APP == INFO:werkzeug:127.0.0.1 - - [09/Oct/2024 20:48:48] "POST /cook HTTP/1.1" 200 -
```

TODO: Add information about VPNs and Firewalls

You may have noticed that we are updating the event information on every new steo we take, but it is not getting saved to our Redis state store. Let's fix this in the next challenge: **Pub/Sub**!

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

### Installing the dependencies

Navigate to `python/pizza-delivery`. Let's install our dependencies

Open the file called `requirements.txt`. Add the content below to it:

```text
Flask
dapr
cloudevents
uvicorn
typing-extensions
```

Run the command below to install the dependencies:

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
import random
```

### Creating the app route

Leet's create our route that will tell the kitchen to start cooking the pizza `/cook`. Below **# Application routes #** add the following:

```python
@app.route('/cook', methods=['POST'])
def startCooking():
    order_data = request.json
    logging.info('Cooking order: %s', order_data['order_id'])

    # Start cooking
    start(order_data)
    
    logging.info('Cooking done: %s', order_data['order_id'])
    
    # Set the order as ready
    ready(order_data)

    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'}
```

This route is fairly simple. It is a POST request with the `order` content created in the last challenge. We will start the order and, after it is cooked, we will say it is ready.

Add two helper functions to modify the order to _Cooking_ and to _Ready for delivery_.

```python
def start(order_data):
    # Generate a random prep time between 4 and 7 seconds
    prep_time = random.randint(4, 7)
    
    order_data['prep_time'] = prep_time
    order_data['event'] = 'Cooking'

    time.sleep(prep_time)

    return prep_time

def ready(order_data):
    order_data['event'] = 'Ready for delivery'

    return order_data
```

#### Calling the app route

Let's go back to the _pizza-store_ service. We will create a Service Invocation action to call the `/cook` endpoint from our _pizza-kitchen_ service.

First, update the `createOrder()` function, add the following line after the `save_order((order_id, order_data))` invocation:

```python
 # Start cooking
start_cook(order_data)
```

Now, under **# Dapr Service Invocation #**, add the code below:

```python
def start_cook(order_data):
    # Set base url
    base_url = os.getenv('BASE_URL', 'http://localhost') + ':' + os.getenv(
                    'DAPR_HTTP_PORT', '3500')
    
    # Adding pizza-kitchen's app id as part of the header
    headers = {'dapr-app-id': 'pizza-kitchen', 'content-type': 'application/json'}

    # Adding the endpoint /cook to the base url
    url = '%s/cook' % (base_url)

    # Invoking the service
    result = requests.post(
        url=url,
        data=json.dumps(order_data),
        headers=headers
    )
    print('result: ' + str(result), flush=True)
```

Let's break down the code above.

1. First we are setting the base URL:

```python
base_url = os.getenv('BASE_URL', 'http://localhost') + ':' + os.getenv('DAPR_HTTP_PORT', '3500')
```

Notice that the code above calls a URL with the host `localhost` with the port `3500`. This is not calling the _pizza-kitchen_ service directly, but the sidecar of the _pizza-store_ service. The responsiblity of making the service invocation is passed to the sidecar, as the picture below illustrates:

TODO: ADD PICTURE

2. Then, we add the headers and the endpoint:

```python
# Adding pizza-kitchen's app id as part of the header
headers = {'dapr-app-id': 'pizza-kitchen', 'content-type': 'application/json'}

# Adding the endpoint /cook to the base url
url = '%s/cook' % (base_url)
```

The code above creates the header that is going to be attached to our request. The most important piece is the `'dapr-app-id': 'pizza-kitchen'`. By adding this to the header and including the route `/cook` to the end of the base URL, the _pizza-store_ sidecar knows exactly the service and route that it needs to invoke.

With this, services only need to communicate to sidecars through localhost and the sidecar handles the discovery capabilities.

3. Finally, we send the request:

```python
# Invoking the service
result = requests.post(
    url=url,
    data=json.dumps(order_data),
    headers=headers
)
print('result: ' + str(result), flush=True)
```

#### Running the application

We now need to run both applications. If the _pizza-store_ service is still running, press **CTRL+C** to stop it. In your terminal, navigate to the folder where the _pizza-store_ `app.py` is located and run the command below:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3500 --resources-path ../../resources  -- python3 app.py
```

Open a new terminal window and mode to the _pizza-kitchen_ folder. Run the command below:

```bash
dapr run --app-id pizza-kitchen --app-protocol http --app-port 8002 --dapr-http-port 3502  -- python3 app.py
```

#### Testing the service

Open a third terminal window and create a new order:

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:8001/orders
```

Navigate to the _pizza-kitchen_ terminal, you should see the following logs pop up:

```zsh
== APP == INFO:root:Cooking order: f75d9c94-155c-40ce-80c1-94296d2b51e9
== APP == INFO:root:Order f75d9c94-155c-40ce-80c1-94296d2b51e9 updated with event: Cooking
== APP == INFO:root:Order f75d9c94-155c-40ce-80c1-94296d2b51e9 is ready for delivery!
== APP == INFO:werkzeug:127.0.0.1 - - [09/Oct/2024 20:48:48] "POST /cook HTTP/1.1" 200 -
```

TODO: Add information about VPNs and Firewalls

You may have noticed that we are updating the event information on every new steo we take, but it is not getting saved to our Redis state store. Let's fix this in the next challenge: **Pub/Sub**!