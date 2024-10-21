# Challenge 3 - Pub/Sub

## Overview

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

## Installing the dependencies

Navigate to `/PizzaDelivery`. Before start coding, let's install our Dapr dependencies.

```bash
cd PizzaDelivery
dotnet add package Dapr.Client
```

## Create the Pub/Sub component

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

## Create the subscription definition

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

## Creating the service

Open `/Controllers/PizzaDeliveryController.cs` Let's add a couple of import statements.

```csharp
using Microsoft.AspNetCore.Mvc;
using Dapr.Client;
```

## Creating the app route

Leet's create our route `/deliver` that will tell the service to start a  delivery for our order. Below **# Application routes #** add the following:

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

Create a new function called `StartDelivery`. This will simply take our order and update it with multiple events, adding a small delay in between calls:

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

## Publishing the event

Now let's publish! We will use the Dapr SDK to submit the event to our PubSub. Under **Dapr pub/sub** add:

```csharp
public async Task<IActionResult> PublishEvent(Order order)
{
  if (order is null)
  {
      return BadRequest();
  }

  DaprClient client = new DaprClientBuilder().Build();

  // create metadata
  var metadata = new Dictionary<string, string> { { "Content-Type", "application/json" } };

  await client.PublishEventAsync(PubSubName, TopicName, order, metadata, cancellationToken: CancellationToken.None);

  return Ok();
}
```

The code above uses the Dapr SDK to publish an event to our PubSub infrastructure (Redis). That event is the `order` in json format.

Our Delivery service is completed. Let's update _pizza-kitchen_ and _pizza-store_. now.

## Sending the Kitchen events

Open `/PizzaKitchen/Controllers/PizzaKitchenController.cs` and add the following lines to the controller class:

```csharp
private readonly string PubSubName = "pizzapubsub";
private readonly string TopicName = "order";
```

Under **Dapr pub/sub**, add the following lines to send our event to the pub/sub:

```csharp
public async Task<IActionResult> PublishEvent(Order order)
{
  if (order is null)
  {
      return BadRequest();
  }

  DaprClient client = new DaprClientBuilder().Build();

  // create metadata
  var metadata = new Dictionary<string, string> { { "Content-Type", "application/json" } };
  await client.PublishEventAsync(PubSubName, TopicName, order, metadata, cancellationToken: CancellationToken.None);

  return Ok();
}
```

Now, Update the `StartCooking` and the `ReadyForDelivery` functions by adding a call to our `PublishEvent`:

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

## Starting a delivery service

Going back to the _pizza-store_ service add the following readyonly strings referencing our pub/sub and the topic we will publish to:

```csharp
private readonly string PubSubName = "pizzapubsub";
private readonly string TopicName = "order";
```

Now, let's add a new service invocation function under **Dapr Service Invocation**. This is the same process from the second challenge, but now we are sending the order to our _pizza-delivery_ service by posting the order to the `/deliver` endpoint. This starts the order delivery:

```csharp
private async Task Deliver(Order order)
{
    var client = DaprClient.CreateInvokeHttpClient(appId: "pizza-delivery");

    var response = await client.PostAsJsonAsync("/deliver", order, cancellationToken: CancellationToken.None);
    Console.WriteLine("Returned: " + response.StatusCode);
}
```

## Publishing and subscribing to events

First, let's change our `PostOrder():` function to publish an event to our pub/sub. Replace the line below:

```csharp
// Save order to state store
await SaveOrderToStateStore(order);

// Start cooking
await Cook(order);
```

By:

```csharp
// publish the order
var client = new DaprClientBuilder().Build();

// create metadata
var metadata = new Dictionary<string, string> { { "Content-Type", "application/json" } };
await client.PublishEventAsync(PubSubName, TopicName, order, metadata, cancellationToken: CancellationToken.None);
```

With this, we are now replacing direct calls to `SaveOrderToStateStore` and `Cook`  with a `PublishEventAsync` process. This will send the events to Redis(our Pub/Sub component). In the next step we will subscribe to these events and save them to our state store.

## Subscribing to events

Let's create the route `/events`. This route was previously specified in our `subscription.yaml` file as the endpoint that will ve triggered once a new event is published to the `orders` topic.

Under **Dapr Pub/Sub** include:

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

The code above picks up the order from the topic, deserializes it saves it to the state store. Based on the type of event, we either send the event to the kitchen or to the delivery service.

## Running the application

We now need to run all three applications. If the _pizza-store_ and the _pizza-kitchen_ services are still running, press **CTRL+C** in each terminal window to stop them. In your terminal, navigate to the folder where the _pizza-store_ `app.py` is located and run the command below:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3501 --resources-path ../resources  -- dotnet run
```

Open a new terminal window and mode to the _pizza-kitchen_ folder. Run the command below:

```bash
dapr run --app-id pizza-kitchen --app-protocol http --app-port 8002 --dapr-http-port 3502 --resources-path ../resources  -- dotnet run
```

Finally, open a  third terminal window and navigate to the _pizza-delivery_ service folder. Run the command below:

```bash
dapr run --app-id pizza-delivery --app-protocol http --app-port 8003 --dapr-http-port 3503 --resources-path ../resources  -- dotnet run
```

> [!IMPORTANT]
> If you are using Consul as a naming resolution service, add `--config ../resources/config/config.yaml` before `-- dotnet run` on your Dapr run command.

Check for the logs for all three services, you should now see the pubsub component loaded:

```bash
INFO[0000] Component loaded: pizzapubsub (pubsub.redis/v1)  app_id=pizza-store instance=diagrid.local scope=dapr.runtime.processor type=log ver=1.14.4
```

## Testing the service


#### Alternatively, you can use _cURL_ to call the endpoints

Open a fourth terminal window and create a new order:

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:8001/orders
```

Navigate to the _pizza-store_ terminal, you should see the following logs pop up with all the events being updated:

```zsh
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

On the parent folder, create a new file called `dapr.yaml`. Add the following content to it:

```yaml
version: 1
common:
  resourcesPath: ./resources
  # Uncomment the following line if you are running Consul for service naming resolution
  # configFilePath: ./resources/config/config.yaml
apps:
  - appDirPath: ./PizzaStore/
    appID: pizza-store
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

## Congratulations

Congratulations in completing all of the three challenges. Stop by our booth to show all challenges completed and get some swag for your hard work!

You have now scratched the surface of what Dapr can do. It's highly recommended navigating to the [Dapr docs](https://docs.dapr.io/) and learning more about it.
