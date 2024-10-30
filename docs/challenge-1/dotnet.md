# Challenge 1 - State Store

## Overview

On our first challenge, we will:

- Create our first Dapr application: _pizza-store_.
- Configure a State Store component for our local Redis instance to save, get, and delete an order.
- Run our app locally using `dapr run`.

To learn more about the State Management Building block, refer to the [Dapr docs](https://docs.dapr.io/developing-applications/building-blocks/state-management/state-management-overview/).

## Configuring the state store

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

This is a component definition file named `pizzastatestore`. In the _spec_ definition, note that the type of the component is `state.redis` and the metadata contains host and password information for our Redis instance that was deployed as a container during Dapr's initialization. process.

## Installing the dependencies

Now navigate to `/PizzaStore`. This folder contains the the files for out first service. Before start coding, let's install our Dapr dependencies.

```bash
cd PizzaStore

dotnet add package Dapr.Client
```

## Creating the service

Inside `Controllers/PizzaStoreController.cs` let's add a couple of import statements.

```csharp
using Microsoft.AspNetCore.Mvc;
using Dapr.Client;
using System.Text.Json;
```

We are now importing _Dapr.Client_ from The Dapr dotnet SDK. That's what we will use to manage the state in our Redis instance.

## Managing state

Let's create three new functions: `SaveOrderToStateStore`, `GetOrderFromStateStore`, and `DeleteOrderFromStateStore`.

Start by added a readonly string to the `PizzaStoreController` class to represent the name of our statestore component defined in the previous step:

```csharp
private readonly string StateStoreName = "pizzastatestore";
```

Under **// -------- Dapr State Store -------- //** add the following lines of code:

```csharp
// save order to state store
private async Task SaveOrderToStateStore(Order order)
{
    var client = new DaprClientBuilder().Build();
    await client.SaveStateAsync(StateStoreName, order.OrderId, order);
    Console.WriteLine("Saving order " + order.OrderId + " with event " + order.Event);

    return;
}

// get order from state store
private async Task<Order> GetOrderFromStateStore(string orderId)
{
    var client = new DaprClientBuilder().Build();
    var order = await client.GetStateEntryAsync<Order>(StateStoreName, orderId);
    Console.WriteLine("Order result: " + order.Value);

    return order.Value;
}

// delete order from state store
private async Task DeleteOrderFromStateStore(string orderId)
{
    var client = new DaprClientBuilder().Build();
    await client.DeleteStateAsync(StateStoreName, orderId);
    Console.WriteLine("Deleted order " + orderId);

    return;
}
```

1. `await client.SaveStateAsync(StateStoreName, order.OrderId, order);` saves the state the Redis using a key/value pair. We need to pass the state store name, the order id as a **key**, and a json representation of the order as a **value**.

2. `await client.GetStateEntryAsync<Order>(StateStoreName, orderId);` retrieves the state from the store. It requires a key and the state store name.

3. `await client.DeleteStateAsync(StateStoreName, orderId);` deletes the state from the store. It also requires a key and the state store name.

## Creating the app routes

Before testing our application, we need to create routes so we are able to manage our state store from the frontend and by calling the REST APIs directly. Add three new routes below **# Application routes #**:

```csharp
// App route: Post order
[HttpPost("/orders", Name = "PostOrder")]
public async Task<ActionResult> PostOrder([FromBody] Order order)
{
    if (order is null)
    {
        return BadRequest();
    }

    // create a new order id
    order.OrderId = Guid.NewGuid().ToString();
    order.Event = "Sent to kitchen";

    Console.WriteLine("Posting order: " + order.Address);

    // Save order to state store
    await SaveOrderToStateStore(order);

    return Ok(order);
}

//App route: Get order by order id
[HttpGet("/orders/{orderId}", Name = "GetOrderByOrderId")]
public async Task<ActionResult<Order>> GetOrderByOrderId(string orderId)
{
    var order = await GetOrderFromStateStore(orderId);
    if (order == null)
    {
        return NotFound();
    }
    return Ok(order);
}

//App route: delete order by order id
[HttpDelete("/orders/{orderId}", Name = "DeleteOrderByOrderId")]
public async Task<ActionResult> DeleteOrderByOrderId(string orderId)
{
    await DeleteOrderFromStateStore(orderId);
    return Ok();
}
```

To save the event we generate a new order UUID and set a new event: _Sent to Kitchen_. We will use these events during the next challenges.

## Running the application

Now, open a terminal and navigate to the folder where `app.py` is located. Run the following command:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3501 --resources-path ../resources  -- dotnet run
```

> [!IMPORTANT]
> If you are using Consul as a naming resolution service, add `--config ../resources/config/config.yaml` before `-- dotnet run` on your Dapr run command.

This command sets:
    - an app-id `pizza-store` to our application
    - the app-protocol `http`
    - an  app-port `8001` for external communication and and http-port `3501` for sidecar communication
    - the resources-path, where our state store component definition file is locatated. This will guarantee that our component is loaded once the app initializes.

Look for the log entry below to guarantee that the state store was loaded successfully:

```bash
INFO[0000] Component loaded: pizzastatestore (state.redis/v1)  app_id=pizza-store instance=diagrid.local scope=dapr.runtime.processor type=log ver=1.14.4
```

## Testing the service

### Create an order

Open `PizzaStore.rest` and place a new order by clicking the button `Send request` under _Place a new order_:

![send-request](/imgs/rest-request.png)

Copy the value of the `order id` returned and replace the value on `@order-id = 7adb27dd-53c3-4f20-be7f-591e155c9f07` with it.

To retrieve and delete the order, run the corresponding requests.

#### Alternatively, you can use _cURL_ to call the endpoints

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

## Next

Let's create a new service to help us cook the pizza to our customers. On the next challenge, you will learn how to create a new endpoint and how to invoke it using Dapr. When you are ready, move to Challenge 2: [Service Invocation](/docs/challenge-2/dotnet.md)!
