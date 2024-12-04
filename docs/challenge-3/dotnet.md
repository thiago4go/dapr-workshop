# Challenge 3 - Pub/Sub

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
- Update _pizza-kitchen_ and _pizza-storefront_ to publish events to the Pub/Sub using the Dapr SDK.
- Create a _subscription_ definition route in the _pizza-storefront_ to save all the state events to the state store.

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

Similar to the `statestore.yaml` file, this new definition creates a Dapr component called _pizzapubsub_ of type _pubsub.redis_ pointing to the local Redis instance, using Redis Streams. Each app will initialize this component to interact with it.

## Create a subscription

Still inside the `/resources` folder, create a new file called `subscription.yaml`. Add the following content to it:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: pizza-storefront-subscription
spec:
  topic: order
  route: /events
  pubsubname: pizzapubsub
scopes: 
- pizza-storefront  
```

This file of kind `Subscription` specifies that every time the Pub/Sub `pizzapubsub` component receives a message in the `orders` topic, this message will be sent to a route called `/events` on the scoped `pizza-storefront` service. By setting `pizza-storefront` as the only scope, we guarantee that this subscription rule will only apply to this service and will be ignored by others. Finally, the `/events` endpoint needs to be created in the `pizza-storefront` service in order to receive the events.

## Install the dependencies

Navigate to `/PizzaDelivery`. Before you start coding, install the Dapr dependencies.

```bash
cd PizzaDelivery
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

Open `/Controllers/PizzaDeliveryController.cs` and add the following import statements.

```csharp
using Microsoft.AspNetCore.Mvc;
using Dapr.Client;
```

Create a private field for the `DaprClient` inside the controller class:

```csharp
private readonly DaprClient _daprClient;
```

Update the `PizzaDeliveryController` constructor to include the `DaprClient` and to set the private field:

```csharp
public PizzaDeliveryController(DaprClient daprClient, ILogger<PizzaDeliveryController> logger)
    {
        _logger = logger;
        _daprClient = daprClient;
    }
```

## Create the app route

Create the route `/deliver` that will instruct the service to start a  delivery for the pizza order. Below **// -------- Application routes -------- //** add the following code:

```csharp
// App route: Post order
[HttpPost("/deliver", Name = "StartCook")]
public async Task<ActionResult> PostOrder([FromBody] Order order)
{
    if (order is null)
    {
        return BadRequest();
    }

    Console.WriteLine("Delivery started: " + order.OrderId);

    await StartDelivery(order);

    Console.WriteLine("Delivery completed: " + order.OrderId);

    return Ok(order);
}
```

Under **// -------- Dapr Pub/Sub -------- //** create a new function called `StartDelivery`. This will take the order and update it with multiple events, adding a small delay in between calls:

```csharp
private async Task StartDelivery(Order order)
{
  // Simulate delivery time and events
  await Task.Delay(3000);
  order.Event = "Delivery started";
  await PublishEvent(order);

  await Task.Delay(3000);
  order.Event = "Order picked up by driver";
  await PublishEvent(order);

  await Task.Delay(5000);
  order.Event = "En-route";
  await PublishEvent(order);

  await Task.Delay(5000);
  order.Event = "Nearby";
  await PublishEvent(order);

  await Task.Delay(5000);
  order.Event = "Delivered";
  await PublishEvent(order);
}
```

## Publish the event

Now its time to publish the events using Dapr! Add the following lines into the controller class to define the Pub/Sub component and topic names:

```csharp
private readonly string PubSubName = "pizzapubsub";
private readonly string TopicName = "order";
```

Use the Dapr SDK to submit the event to the message broker. Under **// -------- Dapr Pub/Sub -------- //** add:

```csharp
public async Task<IActionResult> PublishEvent(Order order)
{
  if (order is null)
  {
      return BadRequest();
  }

  // create metadata
  var metadata = new Dictionary<string, string> { { "Content-Type", "application/json" } };

  await _daprClient.PublishEventAsync(PubSubName, TopicName, order, metadata, cancellationToken: CancellationToken.None);

  return Ok();
}
```

The code above uses the Dapr SDK to publish an event to the PubSub infrastructure (Redis). That event is the `order` in json format.

The `delivery-service` is now completed. Update _pizza-kitchen_ and _pizza-storefront_ now.

## Register the DaprClient for PizzaKitchen

Navigate to the `/PizzaKitchen` folder, open `Program.cs` and add this using statement to the top:

```csharp
using Dapr.Client;
```

In the same file add the `DaprClient` registration to the `ServiceCollection`:

```csharp
builder.Services.AddSingleton<DaprClient>(new DaprClientBuilder().Build());
```

This enables the dependency injection of the DaprClient in other classes.

## Send the Kitchen events

Open `/PizzaKitchen/Controllers/PizzaKitchenController.cs` and create a private field for the `DaprClient` inside the controller class:

```csharp
private readonly DaprClient _daprClient;
```

Update the `PizzaKitchenController` constructor to include the `DaprClient` and to set the private field:

```csharp
public PizzaKitchenController(DaprClient daprClient, ILogger<PizzaKitchenController> logger)
    {
        _logger = logger;
        _daprClient = daprClient;
    }
```

Add the following lines to the controller class:

```csharp
private readonly string PubSubName = "pizzapubsub";
private readonly string TopicName = "order";
```

Under **// -------- Dapr Pub/Sub -------- //**, add the following lines to send the order event to the message broker:

```csharp
public async Task<IActionResult> PublishEvent(Order order)
{
  if (order is null)
  {
      return BadRequest();
  }

  // create metadata
  var metadata = new Dictionary<string, string> { { "Content-Type", "application/json" } };
  await _daprClient.PublishEventAsync(PubSubName, TopicName, order, metadata, cancellationToken: CancellationToken.None);

  return Ok();
}
```

Now, Update the `StartCooking` and the `ReadyForDelivery` functions by adding a call to the `PublishEvent` function:

```csharp
private async Task StartCooking(Order order)
{
  var prepTime = new Random().Next(4, 7);

  order.PrepTime = prepTime;
  order.Event = "Cooking";

  // Send cooking event to pubsub 
  await PublishEvent(order);

  await Task.Delay(prepTime * 1000);

  return;
}

private async Task ReadyForDelivery(Order order)
{
  order.Event = "Ready for delivery";

  // Send cooking event to pubsub 
  await PublishEvent(order);

  return;
}
```

## Call the delivery service

Going back to the `PizzaStoreController` class in the _pizza-storefront_ service add the following ready-only strings referencing the pub/sub component and the topic will be published to:

```csharp
private readonly string PubSubName = "pizzapubsub";
private readonly string TopicName = "order";
```

Add a new service invocation function under **// -------- Dapr Service Invocation -------- //**. This is the same process from the second challenge, but now you will be sending the order to the _pizza-delivery_ service by posting the order to the `/deliver` endpoint. This begins the order delivery:

```csharp
private async Task Deliver(Order order)
{
    var client = DaprClient.CreateInvokeHttpClient(appId: "pizza-delivery");

    var response = await client.PostAsJsonAsync("/deliver", order, cancellationToken: CancellationToken.None);
    Console.WriteLine("Returned: " + response.StatusCode);
}
```

## Publish events

Change the `PostOrder():` function to publish an event to the pub/sub broker. Replace the lines below:

```csharp
// Save order to state store
await SaveOrderToStateStore(order);

// Start cooking
await Cook(order);
```

With the following code block:

```csharp
// create metadata
var metadata = new Dictionary<string, string> { { "Content-Type", "application/json" } };
// publish the order
await _daprClient.PublishEventAsync(PubSubName, TopicName, order, metadata, cancellationToken: CancellationToken.None);
```

With this, you are now replacing direct calls to `SaveOrderToStateStore` and `Cook`  with a `PublishEventAsync` process. This will send the events to the Redis Pub/Sub component. In the next step you will subscribe to these events and save them to the state store.

## Subscribe to events

Create the route `/events` in the _pizza-storefront_ service. This route was previously specified in the `subscription.yaml` file as the endpoint that will be triggered once a new event is published to the `orders` topic.

Under **// -------- Dapr Pub/Sub -------- //** add the following:

```csharp
[HttpPost("/events")]
public async Task<IActionResult> Process([FromBody] JsonDocument rawTransaction)
{
    var order = JsonSerializer.Deserialize<Order>(rawTransaction.RootElement.GetProperty("data").GetRawText());

    if (order is null)
    {
        return BadRequest();
    }

    Console.WriteLine("Processing order: " + order.OrderId);

    await SaveOrderToStateStore(order);

    // check if event is sent to kitchen
    if (order.Event == "Sent to kitchen")
    {
        // Start cooking
        await Cook(order);
    }

    if (order.Event == "Ready for delivery")
    {
        //start delivery
        await Deliver(order);
    }

    return Ok();
}
```

The code above picks up the order from the topic, deserializes it saves it to the state store using Dapr. Based on the type of event, we either send the event to the kitchen or to the delivery service.

## Run the application

It's time to run all three applications. If the _pizza-storefront_ and the _pizza-kitchen_ services are still running, press **CTRL+C** in each terminal window to stop them. In the terminal, navigate to the folder where the _pizza-storefront_ service located and run the command below:

```bash
dapr run --app-id pizza-storefront --app-protocol http --app-port 8001 --dapr-http-port 3501 --resources-path ../resources  -- dotnet run
```

Open a new terminal window and navigate to the _pizza-kitchen_ folder. Run the command below:

```bash
dapr run --app-id pizza-kitchen --app-protocol http --app-port 8002 --dapr-http-port 3502 --resources-path ../resources  -- dotnet run
```

Finally, open a third terminal window and navigate to the _pizza-delivery_ service folder. Run the command below:

```bash
dapr run --app-id pizza-delivery --app-protocol http --app-port 8003 --dapr-http-port 3503 --resources-path ../resources  -- dotnet run
```

> [!IMPORTANT]
> If you are using Consul as a naming resolution service, add `--config ../resources/config/config.yaml` before `-- dotnet run` on your Dapr run command.

Check the Dapr and application logs for all three services. You should now see the pubsub component loaded in the Dapr logs:

```bash
INFO[0000] Component loaded: pizzapubsub (pubsub.redis/v1)  app_id=pizza-storefront instance=diagrid.local scope=dapr.runtime.processor type=log ver=1.14.4
```

## Test the service

### Use VS Code REST Client

Open `PizzaStore.rest` and create a new order, similar to what was done previous challenges.

Navigate to the _pizza-storefront_ terminal, where you should see the following logs pop up with all the events being updated:

```bash
== APP == Posting order: 
== APP == Processing order: ade479f5-7e4a-432c-b2f3-c1fa44241d4d
== APP == Saving order ade479f5-7e4a-432c-b2f3-c1fa44241d4d with event Sent to kitchen
== APP == Processing order: ade479f5-7e4a-432c-b2f3-c1fa44241d4d
== APP == Saving order ade479f5-7e4a-432c-b2f3-c1fa44241d4d with event Cooking
== APP == Processing order: ade479f5-7e4a-432c-b2f3-c1fa44241d4d
== APP == Returned: OK
== APP == Saving order ade479f5-7e4a-432c-b2f3-c1fa44241d4d with event Ready for delivery
== APP == Processing order: ade479f5-7e4a-432c-b2f3-c1fa44241d4d
== APP == Saving order ade479f5-7e4a-432c-b2f3-c1fa44241d4d with event Delivery started
== APP == Processing order: ade479f5-7e4a-432c-b2f3-c1fa44241d4d
== APP == Saving order ade479f5-7e4a-432c-b2f3-c1fa44241d4d with event Order picked up by driver
== APP == Processing order: ade479f5-7e4a-432c-b2f3-c1fa44241d4d
== APP == Saving order ade479f5-7e4a-432c-b2f3-c1fa44241d4d with event En-route
== APP == Processing order: ade479f5-7e4a-432c-b2f3-c1fa44241d4d
== APP == Saving order ade479f5-7e4a-432c-b2f3-c1fa44241d4d with event Nearby
== APP == Processing order: ade479f5-7e4a-432c-b2f3-c1fa44241d4d
== APP == Saving order ade479f5-7e4a-432c-b2f3-c1fa44241d4d with event Delivered
== APP == Returned: OK
```

### Use _cURL_

Open a fourth terminal window and create a new order using cURL:

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:8001/orders
```

## Run the front-end application

Now that you've completed all the challenges, its time to order a pizza using the UI.

With all services still running, navigate to `/PizzaFrontend`, open a new terminal, and run:

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
  resourcesPath: ./resources
  # Uncomment the following line if you are running Consul for service naming resolution
  # configFilePath: ./resources/config/config.yaml
apps:
  - appDirPath: ./PizzaStore/
    appID: pizza-storefront
    daprHTTPPort: 3501
    appPort: 8001
    command: ["dotnet", "run"]
  - appDirPath: ./PizzaKitchen/
    appID: pizza-kitchen
    appPort: 8002
    daprHTTPPort: 3502
    command: ["dotnet", "run"]
  - appDirPath: ./PizzaDelivery/
    appID: pizza-delivery
    appPort: 8003
    daprHTTPPort: 3503
    command: ["dotnet", "run"]
```

Stop the services, if they are running, and enter the following command in the terminal:

```bash
dapr run -f .
```

All three services will run at the same time and log events at the same terminal window.

## Next steps

Congratulations, you have completed all the challenges and you can claim your [reward](../completion.md)!
