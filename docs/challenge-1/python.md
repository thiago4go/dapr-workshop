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

Now navigate to `/pizza-store` and run the command below to install the dependencies:

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

### Running the application

Now, open a terminal and navigate to the folder where `app.py` is located. Run the following command:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 6000 --dapr-http-port 3501 --resources-path ../../resources  -- python3 app.py
```

> [!IMPORTANT]
> If you are using Consul as a naming resolution service, add `--config ../resources/config/config.yaml` before `-- python3 app.py` on your Dapr run command.

This command sets:
    - an app-id `pizza-store` to our application
    - the app-protocol `http`
    - an  app-port `6000` for external communication and and http-port `3501` for sidecar communication
    - the resources-path, where our state store component definition file is locatated. This will guarantee that our component is loaded once the app initializes.

Look for the log entry below to guarantee that the state store was loaded successfully:

```bash
INFO[0000] Component loaded: pizzastatestore (state.redis/v1)  app_id=pizza-store instance=diagrid.local scope=dapr.runtime.processor type=log ver=1.14.4
```

### Testing the service

#### Create an order

Open `PizzaStore.rest` and place a new order by clicking the button `Send request` under _#Place a new order_:

![send-request](/imgs/rest-request.png)

Copy the value of the `order id` returned and replace the value on `@order-id = 7adb27dd-53c3-4f20-be7f-591e155c9f07` with it.

To retrieve and delete the order, run the corresponding requests.

#### Alternatively, you can use _cURL_ to call the endpoints:**

Run the command below to create a new order.

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:6000/orders
```

If you downloaded Redis Insight, you can visualize the new entry there:

![redis-insight](/imgs/redis-insight.png)

Take note of the new order-id generated and run the following command to get the newly created order:

```bash
curl -H 'Content-Type: application/json' \
    -X GET \
    http://localhost:6000/orders/<order-id>
```

Finally, to delete the order:

```bash
curl -H 'Content-Type: application/json' \
    -X DELETE \
    http://localhost:6000/orders/<order-id>
```
