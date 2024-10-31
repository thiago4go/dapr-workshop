# Challenge 2 - Service Invocation

## Overview

On our second challenge, we will send the order created in the previous step to the kitchen! For that, we will:

- Create a new service called _pizza-kitchen_ with a `/cook` endpoint.
- Update _pizza-store_ to invoke the `/cook` endpoint with the Service Invocation building block.

To learn more about the Service Invocation building block, refer to the [Dapr docs](https://docs.dapr.io/developing-applications/building-blocks/service-invocation/).

### Installing the dependencies

Open a new terminal window and create another virtual enviroment:

```bash
python -m venv env
source env/bin/activate
```

Navigate to `/pizza-kitchen` and run the command below to install the dependencies:

```bash
pip install -r requirements.txt
```

## Creating the service

Open `app.py`. Add the import statements below:

```python
from flask import Flask, request, jsonify
from dapr.clients import DaprClient

import json
import time
import logging
import random
```

## Creating the app route

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

    return jsonify({'success': True})
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

## Calling the app route

Let's go back to the _pizza-store_ service. We will create a Service Invocation action to call the `/cook` endpoint from our _pizza-kitchen_ service.

First, update the `createOrder()` function, add the following line after the `save_order((order_id, order_data))` invocation:

```python
 # Start cooking
start_cook(order_data)
```

Now, under **# Dapr Service Invocation #**, add the code below:

```python
def start_cook(order_data):
    with DaprClient() as client:
        response = client.invoke_method(
            'pizza-kitchen',
            'cook',
            http_verb='POST',
            data=json.dumps(order_data),
        )
        print('result: ' + response.text(), flush=True)
```

Let's break down the code above.

1. First we creating an instance of the DaprClient.

```python
with DaprClient() as client:
```

2. The `invoke_method` function is used to send a request to another application.

Notice that the parameters provided to the invoke_method do not include any url. It contains the application ID of the targer application (_pizza-kitchen_) and the method to invoke (`cook`). This application will not invoke the `cook` method on the _pizza-kitchen_ application directly. The Dapr sidecar of the _pizza-store_ application makes a call to the Dapr sidecar of the _pizza-kitchen_ application. The _pizza-store_ sidecar will find the location of the _pizza-kitchen_ sidecar via a name resolution component. More info about different name resolution components can be found in the [Dapr docs](https://docs.dapr.io/reference/components-reference/supported-name-resolution/). The responsiblity of making the service invocation is passed to the sidecar, as the picture below illustrates:

![service-invocation](/imgs/service-invocation.png)

With this, services only need to communicate to sidecars through localhost and the sidecar handles the discovery capabilities.

## Running the application

We now need to run both applications. If the _pizza-store_ service is still running, press **CTRL+C** to stop it. In the terminal for the _pizza-store_, ensure you're still in the _pizza-store_ folder where `app.py` is located and run the command below:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3501 --resources-path ../resources  -- python3 app.py
```

In the terminal for the  _pizza-kitchen_ application ensure you are in the _pizza-kitchen_ folder and run the command below:

```bash
dapr run --app-id pizza-kitchen --app-protocol http --app-port 8002 --dapr-http-port 3502  -- python3 app.py
```

> [!IMPORTANT]
> If you are using Consul as a naming resolution service, add `--config ../resources/config/config.yaml` before `-- python3 app.py` on your Dapr run command.

## Testing the service

### Create an order

Open `PizzaStore.rest` and place a new order by clicking the button `Send request` under _Place a new order_:

![send-request](/imgs/rest-request.png)

### Alternatively, open a third terminal window and create a new order:

Open a third terminal window and create a new order:

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:8001/orders
```

Navigate to the _pizza-kitchen_ terminal, you should see the following logs pop up:

```bash
== APP == INFO:root:Cooking order: e0bfa96e-08e5-43be-bba6-4ebe0b6baef7
== APP == INFO:root:Cooking done: e0bfa96e-08e5-43be-bba6-4ebe0b6baef7
== APP == INFO:werkzeug:127.0.0.1 - - [09/Oct/2024 20:48:48] "POST /cook HTTP/1.1" 200 -
```

## Next

You may have noticed that we are updating the event information on every new step we take, but it is not getting saved to our Redis state store. Let's fix this in the next challenge: [Pub/Sub](/docs/challenge-3/python.md)!
