# Challenge 1 - State Store

## Overview

> Ensure you have completed the [technical prerequisites](../prerequisites.md) before starting the challenges.

In this challenge, you will:

- Configure a State Store component using a local Redis instance to save, get, and delete a pizza order.
- Update the `pizza-store` application to use the Dapr State Management API.
- Run the app locally using the Dapr CLI.

<img src="../../imgs/challenge-1.png" width=50%>

To learn more about the Dapr State Management Building Block, refer to the [Dapr docs](https://docs.dapr.io/developing-applications/building-blocks/state-management/state-management-overview/).

## Configure the state store

In your newly cloned `dapr-workshop-python` repository, navigate to the `/resources` folder and create a new file called `statestore.yaml`. Add the content below to the file:

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

This is a Dapr Component specification file named `pizzastatestore`. In the _spec_ definition, note that the type of the component is `state.redis` and the metadata contains host and password information for the local Redis instance that was deployed as a container during Dapr's initialization process.

## Install dependencies

Now navigate to the `/pizza-store` directory. This folder contains all the files you need for your first service. Before beginning to code, install the Dapr dependencies by running the following in a new terminal window:

```bash
cd pizza-store
pip install -r requirements.txt
```

## Create the service

Open `/pizza-store/app.py`. Update all the `from` and `import` lines:

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
from dapr.clients import DaprClient

import uuid
import logging
import json
```

This will import _DaprClient_ from _dapr.clients_. That is what you will use to manage the state in the Redis instance.

## Manage state

Create three new functions: `save_order`, `get_order`, and `delete_order`.

Start by creating a const that refers to the state store component:

```python
DAPR_STORE_NAME = 'pizzastatestore'
```

The name given to this const is the same name configured in the `statestore.yaml` file, created in the step above.

Under **# Dapr State Store #** add the following lines of code:

```python
def save_order(order_id, order_data):
    with DaprClient() as client:
        # Save state 
        client.save_state(DAPR_STORE_NAME, order_id, json.dumps(order_data))
        logging.info('Saving Order %s with event %s', order_id, order_data['event'])

        return order_id

def get_order(order_id):
    with DaprClient() as client:
        # Get state
        result = client.get_state(DAPR_STORE_NAME, order_id)
        logging.info('Order result - %s', str(result.data))

        return json.loads(result.data)
    
def delete_order(order_id):
    with DaprClient() as client:
        # Delete state
        client.delete_state(DAPR_STORE_NAME, order_id)
        logging.info('Order deleted - %s', order_id)

        return order_id
```

The Dapr Client is responsible for the following, respectively:

1. `client.save_state(DAPR_STORE_NAME, order_id, str(order_data))`; saves the state the Redis using a key/value pair. It requires the state store name, the order id as a **key**, and a json representation of the order as a **value**.

2. `result = client.get_state(DAPR_STORE_NAME, order_id)`; retrieves the state from the store. It requires a key and the state store name.

3. `client.delete_state(DAPR_STORE_NAME, order_id)`; deletes the state from the store. It also requires a key and the state store name.

## Create the app routes

Before testing the application, create routes to be used by the state store from the frontend and to call the REST APIs directly. Add three new routes below **# Application routes #**:

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

    return jsonify({'orderId': order_id})

# Get order by id
@app.route('/orders/<order_id>', methods=['GET'])
def getOrder(order_id):
    if order_id:
        result = get_order(order_id)

        return jsonify(result)
    
    return jsonify({'success': False, 'message': 'Missing order id'}), 404

# Delete order by id
@app.route('/orders/<order_id>', methods=['DELETE'])
def deleteOrder(order_id):
    if order_id:
        delete_order(order_id)   

        return jsonify({'orderId': order_id})
    
    return jsonify({'success': False, 'message': 'Missing order id'}), 404
```

To save the event a new order UUID is generated and set a new event: _Sent to Kitchen_. You will use these events in upcoming challenges.

## Run the application

Now, open a terminal and navigate to the `/pizza-store` folder where `app.py` is located. Use the Dapr CLI to run the following command:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3501 --resources-path ../resources  -- python3 app.py
```

> [!IMPORTANT]
> If you are using Consul as a naming resolution service, add `--config ../resources/config/config.yaml` before `-- python3 app.py` on your Dapr run command.

This command sets:
  - the app-id as `pizza-store`
  - the app-protocol to `http`
  - an app-port of `8001` for Dapr communication into the app
  - an http-port of `3501` for Dapr API communication from the app
  - the resources-path, where the state store component definition file is located. This will guarantee that the Redis component is loaded when the app initializes.

Look for the log entry below to guarantee that the state store component was loaded successfully:

```bash
INFO[0000] Component loaded: pizzastatestore (state.redis/v1)  app_id=pizza-store instance=diagrid.local scope=dapr.runtime.processor type=log ver=1.14.4
```

## Test the service

### Use VS Code REST Client

Open the `PizzaStore.rest` file located in the root of the repository and place a new order by clicking the button `Send request` under _Place a new order_:

![send-request](/imgs/rest-request.png)

Once an order is posted, the _Order ID_ is extracted from the response body and assigned to the @order-id variable:

```bash
@order-id={{postRequest.response.body.orderId}}
```

This allows you to immediately run a `GET` or `DELETE` request with the correct _Order ID_. To retrieve and delete the order, run the corresponding requests.

#### Use _cURL_

Run the command below to create a new order.

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:8001/orders
```

Copy the order-id generated and run the following command to get the newly created order:

```bash
curl -H 'Content-Type: application/json' \
    -X GET \
    http://localhost:8001/orders/<order-id>
```

Finally, delete the order:

```bash
curl -H 'Content-Type: application/json' \
    -X DELETE \
    http://localhost:8001/orders/<order-id>
```

### Visualize the data

If you downloaded Redis Insight, you can visualize the new order there:

![redis-insight](/imgs/redis-insight.png)

## Next steps

Create a new service to cook the pizza. In the next challenge, you will learn how to create a new API endpoint and how to invoke it using Dapr. When you are ready, go to Challenge 2:: [Service Invocation](/docs/challenge-2/python.md)!
