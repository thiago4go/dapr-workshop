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

In your newly cloned `dapr-workshop-csharp` repository, navigate to the `/resources` folder and create a new file called `statestore.yaml`. Add the content below to the file:

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

Navigate to the `/PizzaStore` directory. This folder contains all the files you need for your first service. Before beginning to code, install the Dapr dependencies by running the following in a new terminal window:

```bash
cd PizzaStore

dotnet add package Dapr.Client
```

## Register the DaprClient

Open `Program.cs` and add this using statement to the top:

```csharp
using Dapr.Client;
```

In the same file add the `DaprClient` registration to the `ServiceCollection`:

```csharp
builder.Services.AddSingleton<DaprClient>(new DaprClientBuilder().Build());
```

This enables the dependency injection of the `DaprClient` in other classes.

## Create the service

Inside `Controllers/PizzaStoreController.cs` let's add a couple of import statements.

```csharp
using Microsoft.AspNetCore.Mvc;
using Dapr.Client;
using System.Text.Json;
```

This will import the _Dapr.Client_ library from the [Dapr Dotnet SDK](https://github.com/dapr/dotnet-sdk). That is what you will use to manage the state in the Redis instance.

Create a private field for the `DaprClient` inside the controller class:

```csharp
private readonly DaprClient _daprClient;
```

Update the `PizzaStoreController` constructor to include the `DaprClient` and to set the private field:

```csharp
public PizzaStoreController(DaprClient daprClient, ILogger<PizzaStoreController> logger)
    {
        _logger = logger;
        _daprClient = daprClient;
    }
```

## Manage state

Create three new functions: `SaveOrderToStateStore`, `GetOrderFromStateStore`, and `DeleteOrderFromStateStore`.

Start by adding a readonly string to the `PizzaStoreController` class to represent the name of the Dapr state store component defined in the previous step. This name **must** be the same as the `metadata.name` in the Dapr component spec.

```csharp
private readonly string StateStoreName = "pizzastatestore";
```

Under **// -------- Dapr State Store -------- //** add the following lines of code:

```csharp
// save order to state store
private async Task SaveOrderToStateStore(Order order)
{
    await _daprClient.SaveStateAsync(StateStoreName, order.OrderId, order);
    Console.WriteLine("Saving order " + order.OrderId + " with event " + order.Event);

    return;
}

// get order from state store
private async Task<Order> GetOrderFromStateStore(string orderId)
{
    var order = await _daprClient.GetStateEntryAsync<Order>(StateStoreName, orderId);
    Console.WriteLine("Order result: " + order.Value);

    return order.Value;
}

// delete order from state store
private async Task DeleteOrderFromStateStore(string orderId)
{
    await _daprClient.DeleteStateAsync(StateStoreName, orderId);
    Console.WriteLine("Deleted order " + orderId);

    return;
}
```

The Dapr Client is responsible for the following, respectively:

1. `await _daprClient.SaveStateAsync(StateStoreName, order.OrderId, order);` saves the state to Redis using a key/value pair. It requires the state store name, the order id as a **key**, and a json representation of the order as a **value**.

2. `await _daprClient.GetStateEntryAsync<Order>(StateStoreName, orderId);` retrieves the state from the store. It requires a key and the state store name.

3. `await _daprClient.DeleteStateAsync(StateStoreName, orderId);` deletes the state from the store. It also requires a key and the state store name.

## Create the app routes

Before testing the application, create routes to be used by the state store from the frontend and to call the REST APIs directly. Add three new routes below **// -------- Application routes -------- //**:

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

To save the event generate a new order GUID and set a new event: _Sent to Kitchen_. You will use these events in upcoming challenges.

## Run the application

Open a new terminal and navigate to the `/PizzaStore` folder. Use the Dapr CLI to run the following command:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3501 --resources-path ../resources  -- dotnet run
```

> [!IMPORTANT]
> If you are using Consul as a name resolution service, add `--config ../resources/config/config.yaml` before `-- dotnet run` in your Dapr run command.

This command sets:
    - the app-id as `pizza-store`
    - the app-protocol to `http`
    - an app-port of `8001` for Dapr communication into the app
    - an http-port of `3501` for Dapr API communication from the app
    - the resources-path, where the state store component definition file is located. This will guarantee that the Redis component is loaded when the app initializes.

Look for the log entry below to ensure that the state store component was loaded successfully:

```bash
...
INFO[0000] Component loaded: pizzastatestore (state.redis/v1)  app_id=pizza-store instance=diagrid.local scope=dapr.runtime.processor type=log ver=1.14.4
...
```

## Test the service

### Use VS Code REST Client

Open the `PizzaStore.rest` file located in the root of the repository and place a new order by clicking the button `Send request` under _Place a new order_:

![send-request](/imgs/rest-request.png)

Once an order is posted, the _Order ID_ is extracted from the response body and assigned to the @order-id variable:

```bash
@order-id = {{postRequest.response.body.order_id}}
```

This allows you to immediately run a `GET` or `DELETE` request with the correct _Order ID_. To retrieve and delete the order, run the corresponding requests.

### Use _cURL_

Run the command below to create a new order:

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

Create a new service to cook the pizza. In the next challenge, you will learn how to create a new API endpoint and how to invoke it using Dapr. When you are ready, go to Challenge 2: [Service Invocation](/docs/challenge-2/dotnet.md)!
