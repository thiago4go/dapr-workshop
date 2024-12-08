# Challenge 3 - Pub/Sub

## Overview

On the third challenge, your goal is to update the state store with all the events from pizza order that we are generating from the storefront, kitchen, and delivery services. For that, you will:

- Send all the generated events to a new Dapr component, a pub/sub message broker
- Update the storefront, kitchen, and delivery services to publish a message to the pub/sub.
- Subscribe to these events in the order service, which is already managing the order state in our state store.

<img src="../../imgs/challenge-3.png" width=25%>

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
scopes:
- pizza-storefront
- pizza-kitchen
- pizza-delivery
- pizza-order
```

Similar to the `statestore.yaml` file, this new definition creates a Dapr component called _pizzapubsub_ of type _pubsub.redis_ pointing to the local Redis instance, using Redis Streams. Each app will initialize this component to interact with it.

## Create a subscription

Still inside the `/resources` folder, create a new file called `subscription.yaml`. Add the following content to it:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: pizza-subscription
spec:
  topic: orders
  route: /orders-sub
  pubsubname: pizzapubsub
scopes: 
- pizza-order
```

This file of kind `Subscription` specifies that every time the Pub/Sub `pizzapubsub` component receives a message in the `orders` topic, this message will be sent to a route called `/orders-sub` on the scoped `pizza-order` service. By setting `pizza-storefront` as the only scope, we guarantee that this subscription rule will only apply to this service and will be ignored by others. Finally, the `/orders-sub` endpoint needs to be created in the `pizza-order` service in order to receive the events.

## Install the dependencies

Navigate to root of your solution. Before you start coding, install the Dapr dependencies to the `pizza-kitchen` and the `pizza-delivery` services. The `pizza-storefront` service already has the dependencies from challenge 2.

```bash
# Create virtual environment
python3 -m venv env
source env/bin/activate

# Navigate to the service folder and add the Dapr package
cd pizza-storefront
pip install -r requirements.txt

cd ..

# Navigate to the service folder and add the Dapr package
cd pizza-kitchen
pip install -r requirements.txt

cd ..

# Navigate to the service folder and add the Dapr package
cd pizza-delivery
pip install -r requirements.txt

cd ..
```

## Update the Kitchen service to publish messages to the message broker

1. Inside the `pizza-kitchen` folder, navigate to `app.py`. Import the DaprClient:

```python
from dapr.clients import DaprClient
```

2. Add two constants to hold the names of the pub/sub component and topic you will be publishing the messages to:

```python
DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'orders'
```

3. Finally, update the `cook_pizza` method. Replace the  `#TODO` with:

```python
with DaprClient() as client:
  for stage, duration in stages:
      order_data['status'] = f'cooking_{stage}'
      logger.info(f"Order {order_data['order_id']} - {stage}")
      
      # Publish status update
      client.publish_event(
          pubsub_name=DAPR_PUBSUB_NAME,
          topic_name=DAPR_PUBSUB_TOPIC_NAME,
          data=json.dumps(order_data)
      )
      
      time.sleep(duration)
```

The just like the previous challenges, we are using the Dapr Client to call the pub/sub API:

```python
client.publish_event(
  pubsub_name=DAPR_PUBSUB_NAME,
  topic_name=DAPR_PUBSUB_TOPIC_NAME,
  data=json.dumps(order_data)
)
```

In this case, `publish_event` will publish the message `order_data` to the `DAPR_PUBSUB_NAME` and `DAPR_PUBSUB_TOPIC_NAME` you've declared above.

Let's do the same for the Delivery and Storefront services.

## Update the Delivery service to publish messages to the message broker

1. Inside the `pizza-delivery` folder, navigate to `app.py`. Import the DaprClient:

```python
from dapr.clients import DaprClient
```

2. Add two constants to hold the names of the pub/sub component and topic you will be publishing the messages to:

```python
DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'orders'
```

3. Finally, update the `deliver_pizza` method. Replace the  `#TODO` with:

```python
with DaprClient() as client:
  for stage, duration in stages:
      order_data['status'] = f'delivery_{stage}'
      logger.info(f"Order {order_data['order_id']} - {stage}")
      
      # Publish status update
      client.publish_event(
          pubsub_name=DAPR_PUBSUB_NAME,
          topic_name=DAPR_PUBSUB_TOPIC_NAME,
          data=json.dumps(order_data)
      )
      
      time.sleep(duration)
```

## Update the Storefront service to publish messages to the message broker

1. Inside the `pizza-storefront` service folder, navigate to `app.py` and add the pub/sub constants:

```python
DAPR_PUBSUB_NAME = 'pizzapubsub'
DAPR_PUBSUB_TOPIC_NAME = 'orders'
```

2. Inside the `process_order` function update the `# TODO: Publish the status update to the message broker` with:

```python
with DaprClient() as client:
  for stage, duration in stages:
      order_data['status'] = stage
      logger.info(f"Order {order_data['order_id']} - {stage}")
      
      # Publish status update
      client.publish_event(
          pubsub_name=DAPR_PUBSUB_NAME,
          topic_name=DAPR_PUBSUB_TOPIC_NAME,
          data=json.dumps(order_data)
      )
      
      time.sleep(duration)
```

Keep the service invocation code as well. After we publish the `pizza-storefront` events, we still need to invoke the `/cook` and `/deliver`

## Subscribe to events

Now that you've published the events to the topic `orders` in the message broker, you will subscribe to the same topic in the `pizza-order` service:

1. Navigate to the `pizza-order` service folder. Inside `app.py` find the  the route `/order-sub`:

```python
@app.route('/orders-sub', methods=['POST'])
```

2. Replace  the `# TODO: Update the order state` line with:

```python
# Save order state
with DaprClient() as client:
    # Get existing order data if any
    state_key = f"order_{order_id}"
    try:
        state = client.get_state(
            store_name=DAPR_STORE_NAME,
            key=state_key
        )
        existing_order = json.loads(state.data) if state.data else {}
    except Exception:
        existing_order = {}
    
    # Update with new data
    updated_order = {**existing_order, **order_data}
    
    # Save updated state
    client.save_state(
        store_name=DAPR_STORE_NAME,
        key=state_key,
        value=json.dumps(updated_order)
    )
    
    logger.info(f"Updated state for order {order_id}")
```

The code above is fetching the order state and updating it if it exists.

Following the `subscription.yaml` file spec, every time a new message lands in the `orders` topic within the `pizzapubsub` pub/sub, it will be routed to this `/orders-sub` topic. The message will then be sent to the previously created function that creates or updates the message in the state store, created in the first challenge.

```yaml
spec:
  topic: orders
  route: /orders-sub
  pubsubname: pizzapubsub
```

## Run the application

It's time to run all four applications. If the `pizza-storefront`, `pizza-kitchen`, `pizza-delivery`, and the `pizza-order` services are still running, press **CTRL+C** in each terminal window to stop them.

1. Open a new terminal window, navigate to the `/pizza-order` folder and run the command below:

```bash
dapr run --app-id pizza-order --app-protocol http --app-port 8001 --dapr-http-port 3501  --resources-path ../resources -- python3 app.py
```

1. In your terminal, ensure you are in the `/pizza-storefront` folder and run the command below:

```bash
dapr run --app-id pizza-storefront --app-protocol http --app-port 8002 --dapr-http-port 3502  --resources-path ../resources -- python3 app.py
```

2. Open a new terminal window and navigate to `/pizza-kitchen` folder. Run the command below:

```bash
dapr run --app-id pizza-kitchen --app-protocol http --app-port 8003 --dapr-http-port 3503  --resources-path ../resources -- python3 app.py
```

3. Open a third terminal window and navigate to `/pizza-delivery` folder. Run the command below:

```bash
dapr run --app-id pizza-delivery --app-protocol http --app-port 8004 --dapr-http-port 3504  --resources-path ../resources -- python3 app.py
```


> [!IMPORTANT]
> If you are using Consul as a naming resolution service, add `--config ../resources/config/config.yaml` before `-- dotnet run` on your Dapr run command.

Check the Dapr and application logs for all four services. You should now see the pubsub component loaded in the Dapr logs:

```bash
INFO[0000] Component loaded: pizzapubsub (pubsub.redis/v1)  app_id=pizza-storefront instance=diagrid.local scope=dapr.runtime.processor type=log ver=1.14.4
```

## Test the service

### Use VS Code REST Client

Open `Endpoints.http` and create a new order sending the request on `Direct Pizza Store Endpoint (for testing)`, similar to what was done previous challenge.

Navigate to the `pizza-order` terminal, where you should see the following logs pop up with all the events being updated:

```bash
== APP == INFO:__main__:Received order update for order 123: validating
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:40:46] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: processing
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:40:47] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: confirmed
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:40:49] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: validating
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:42:24] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: processing
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:42:25] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: confirmed
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:42:27] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: validating
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:44:36] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: processing
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:44:37] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: confirmed
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:44:39] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: cooking_preparing_ingredients
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:44:40] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: cooking_making_dough
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:44:42] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: cooking_adding_toppings
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:44:45] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: cooking_baking
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:44:47] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: cooking_quality_check
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:44:52] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: delivery_finding_driver
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:44:53] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: delivery_driver_assigned
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:44:55] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: delivery_picked_up
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:44:56] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: delivery_on_the_way
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:44:58] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: delivery_arriving
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:45:03] "POST /orders-sub HTTP/1.1" 200 -
== APP == INFO:__main__:Received order update for order 123: delivery_at_location
== APP == INFO:__main__:Updated state for order 123
== APP == INFO:werkzeug:127.0.0.1 - - [05/Dec/2024 22:45:05] "POST /orders-sub HTTP/1.1" 200 -
```

### Use _cURL_

Open a fourth terminal window and create a new order using cURL:

```bash
curl -H 'Content-Type: application/json' \
   -d '{ "orderId": "1", "pizzaType": "pepperoni", "size": "large", "customer": { "name": "John Doe", "address": "123 Main St", "phone": "555-0123" } }' \
    -X POST \
     http://localhost:8002/order
```

## Dapr multi-app run

Instead of opening multiple terminals to run the services, you can take advantage of a great Dapr CLI feature: [multi-app run](https://docs.dapr.io/developing-applications/local-development/multi-app-dapr-run/multi-app-overview/). This enables you run all three services with just one command!

In the parent folder, create a new file called `dapr.yaml`. Add the following content to it:

```yaml
version: 1
common:
  resourcesPath: ./resources
  # Uncomment the following line if you are running Consul for service naming resolution
  # configFilePath: ./resources/config/config.yaml
apps:
  - appDirPath: ./pizza-order/
    appID: pizza-order
    daprHTTPPort: 3501
    appPort: 8001
    command: ["python3", "app.py"]
  - appDirPath: ./pizza-storefront/
    appID: pizza-storefront
    daprHTTPPort: 3502
    appPort: 8002
    command: ["python3", "app.py"]
  - appDirPath: ./pizza-kitchen/
    appID: pizza-kitchen
    appPort: 8003
    daprHTTPPort: 3503
    command: ["python3", "app.py"]
  - appDirPath: ./pizza-delivery/
    appID: pizza-delivery
    appPort: 8004
    daprHTTPPort: 3504
    command: ["python3", "app.py"]
```

Stop the services, if they are running, and enter the following command in the terminal:

```bash
dapr run -f .
```

All four services will run at the same time and log events at the same terminal window.

## Next steps

In the next challenge we will orchestrate the pizza ordering, cooking, and delivering process leberaging Dapr's Workflow API. Once you are ready, navigate to Challenge 4: [Workflows](/docs/challenge-4/python.md)!
