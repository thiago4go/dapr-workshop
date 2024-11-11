# Challenge 2 - Service Invocation

## Overview

In this challenge, you will send the order created in the previous step to be cooked in the kitchen. For that, you will:

- Create a new service called _pizza-kitchen_ with a `/cook` endpoint.
- Update `pizza-store` to invoke the `/cook` endpoint using the Dapr Service Invocation API.

<img src="../../imgs/challenge-2.png" width=50%>

To learn more about the Dapr Service Invocation building block, refer to the [Dapr docs](https://docs.dapr.io/developing-applications/building-blocks/service-invocation/).

### Install the dependencies

Open a new terminal window and create another virtual environment:

```bash
python -m venv env
source env/bin/activate
```

Navigate to the `/pizza-kitchen` directory. Before you start coding, install the dependencies:

```bash
pip install -r requirements.txt
```

## Create the service

Open `app.py`. Add these import statements:

```python
from flask import Flask, request, jsonify
from dapr.clients import DaprClient

import json
import time
import logging
import random
```

## Create the app route

Create the route `/cook` that will tell the kitchen to start cooking the pizza. Below **# Application routes #** add the following code:

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

    return jsonify({'success': True})
```

This function is fairly simple. It takes in a POST request with the `order` content created in the previous challenge. The order preparation is started and marked as ready with two helper functions. In these functions the order is updated with status events _Cooking_ and _Ready for delivery_.

Add two helper functions to set the order to a status of _Cooking_ and _Ready for delivery_:

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

## Call the app route

Navigate back to the _pizza-store_ service. Construct a Dapr Service Invocation call to the `/cook` endpoint on the _pizza-kitchen_ service.

First, add a new import statement to the file:

```python
import requests
```

Then, update the `createOrder()` function by adding the following line after the `save_order(order_id, order_data)` invocation:

```python
 # Start cooking
start_cook(order_data)
```

Now, under **# Dapr Service Invocation #**, add the code below:

```python
def start_cook(order_data):
    app_id = 'pizza-kitchen'
    headers = {'dapr-app-id': app_id, 'content-type': 'application/json'}
    
    base_url = 'http://localhost'
    dapr_http_port = 3501
    method = 'cook'
    target_url = '%s:%s/%s' % (base_url, dapr_http_port, method)

    response = requests.post(
        url=target_url,
        data=json.dumps(order_data),
        headers=headers
    )
    print('result: ' + response.text, flush=True)
```

Breaking down the code above:

1. First the HTTP headers are defined:

```python
headers = {'dapr-app-id': app_id, 'content-type': 'application/json'}
```

The Dapr sidecar will use the information in the `dapr-app-id` to discover the location of the _pizza-kitchen_ app.

2. The `target_url` is created that will be invoked:

```python
target_url = '%s:%s/%s' % (base_url, dapr_http_port, method)
```

This starts with localhost, since the _pizza-store_ Dapr sidecar is running there, the port of this Dapr sidecar (`3501`), and the method that will be called (`cook`) on the _pizza-kitchen_ app. 

3. Finally the `requests.post` method is used to combine the `target_url`, `order_data` payload and the `headers`:

 ```python
 response = requests.post(
        url=target_url,
        data=json.dumps(order_data),
        headers=headers
```

This method will not invoke the `cook` method on the _pizza-kitchen_ application directly. The Dapr sidecar of the _pizza-store_ application makes a call to the Dapr sidecar of the _pizza-kitchen_ application. The responsiblity of making the service invocation call is then passed to the sidecar, as the picture below illustrates:

![service-invocation](/imgs/service-invocation.png)

This way, services only need to communicate to their associated sidecar over localhost and the sidecar handles the service discovery and invocation capabilities.

## Run the application

It's now time to run both applications. If the _pizza-store_ service is still running, press **CTRL+C** to stop it. In the terminal for the _pizza-store_, ensure you're still in the _pizza-store_ folder where `app.py` is located and run the command below:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3501 --resources-path ../resources  -- python3 app.py
```

In the terminal for the  _pizza-kitchen_ application ensure you are in the _pizza-kitchen_ folder and run the command below:

```bash
dapr run --app-id pizza-kitchen --app-protocol http --app-port 8002 --dapr-http-port 3502  -- python3 app.py
```

> [!IMPORTANT]
> If you are using Consul as a naming resolution service, add `--config ../resources/config/config.yaml` before `-- python3 app.py` on your Dapr run command.

## Test the service

### Use VS Code REST Client

Open `PizzaStore.rest` and create a new order, similar to what was done on the first challenge.

### Alternatively, open a third terminal window and create a new order:

Open a third terminal window and create a new order:

Navigate to the _pizza-kitchen_ terminal, you should see the following logs pop up:

```bash
== APP == INFO:root:Cooking order: e0bfa96e-08e5-43be-bba6-4ebe0b6baef7
== APP == INFO:root:Cooking done: e0bfa96e-08e5-43be-bba6-4ebe0b6baef7
== APP == INFO:werkzeug:127.0.0.1 - - [09/Oct/2024 20:48:48] "POST /cook HTTP/1.1" 200 -
```

### Use  _cURL_

Alternatively, open another terminal window and create a new order via cURL:

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:8001/orders
```

## Next Steps

Now that the services are updating the event information for every order step, you need to make sure that this information is being updated in the Redis state store. You will do this in the next challenge using Dapr [Pub/Sub](/docs/challenge-3/python.md)!
