# Challenge 2 - Service Invocation

## Overview

In this challenge, you will send the order created in the previous step to be cooked in the kitchen. For that, you will:

- Create a new service called _pizza-kitchen_ with a `/cook` endpoint.
- Update `pizza-store` to invoke the `/cook` endpoint using the Dapr Service Invocation API.

<img src="../../imgs/challenge-2.png" width=50%>

To learn more about the Dapr Service Invocation building block, refer to the [Dapr docs](https://docs.dapr.io/developing-applications/building-blocks/service-invocation/).

## Install the dependencies

Navigate to the `/PizzaKitchen` directory. Before you start coding, install the Dapr dependencies by running the following in a new terminal window:

```bash
cd PizzaKitchen
dotnet add package Dapr.Client
```

## Create the service

Open `/Controllers/PizzaKitchenController.cs`. Add a couple of import statements:

```csharp
using Microsoft.AspNetCore.Mvc;
using Dapr.Client;
```

## Create the app route

Create the route `/cook` that will tell the kitchen to start cooking the pizza. Below **// -------- Application routes -------- //** add the following code:

```csharp
// App route: Post order
[HttpPost("/cook", Name = "StartCook")]
public async Task<ActionResult> PostOrder([FromBody] Order order)
{
    if (order is null)
    {
        return BadRequest();
    }

    Console.WriteLine("Cooking order: " + order.OrderId);

    await StartCooking(order);

    Console.WriteLine("Cooking done: " + order.OrderId);

    await ReadyForDelivery(order);

    Console.WriteLine("Order ready for delivery: " + order.OrderId);

    return Ok(order);
}
```

This function is fairly simple. It takes in a POST request with the `order` content created in the previous challenge. The order preparation is started and marked as ready with two helper functions. In these functions the order is updated with status events _Cooking_ and _Ready for delivery_.

Add two helper functions to set the order to a status of _Cooking_ and _Ready for delivery_.

```csharp
private async Task StartCooking(Order order)
{
    var prepTime = new Random().Next(4, 7);

    order.PrepTime = prepTime;
    order.Event = "Cooking";
   
    await Task.Delay(prepTime * 1000);

    return;
}

private async Task ReadyForDelivery(Order order)
{
    order.Event = "Ready for delivery";

    return;
}
```

## Call the app route

Navigate back to the _pizza-store_ service. Construct a Dapr Service Invocation call to the `/cook` endpoint on the _pizza-kitchen_ service.

First, update the `PostOrder()` function by adding the following line after the `await SaveOrderToStateStore(order);` invocation:

```csharp
// Start cooking
await Cook(order);
```

Now, under **// -------- Dapr Service Invocation -------- //**, add the code below:

```csharp
private async Task Cook(Order order)
{
    var client = DaprClient.CreateInvokeHttpClient(appId: "pizza-kitchen");

    var response = await client.PostAsJsonAsync("/cook", order, cancellationToken: CancellationToken.None);
    Console.WriteLine("Returned: " + response.StatusCode);
}
```

Breaking down the code above:

1. First the `DaprClient` is used to create an HttpClient Invocation object with the Dapr app id of the service you want to invoke:

```csharp
var client = DaprClient.CreateInvokeHttpClient(appId: "pizza-kitchen");
```

The code above wraps an HTTP call to the host `localhost` with the port `3501`. This is not calling the _pizza-kitchen_ service directly, but rather the sidecar of the _pizza-store_ service. The responsibility of making the service invocation call is then passed to the sidecar, as the picture below illustrates:

![service-invocation](/imgs/service-invocation.png)

2. Then, you make the call to the endpoint `/cook`, passing the _order_ as the body of the POST request:

```csharp
var response = await client.PostAsJsonAsync("/cook", order, cancellationToken: CancellationToken.None);
```

This way, services only need to communicate to their associated sidecar over localhost and the sidecar handles the service discovery and invocation capabilities.

## Run the application

It's now time to run both applications. If the _pizza-store_ service is still running, use **CTRL+C** to stop it. In your terminal, ensure you are in the folder where the _pizza-store_ app is located and run the command below:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3501 --resources-path ../resources  -- dotnet run
```

Open a new terminal window and navigate to the _pizza-kitchen_ folder. Run the command below:

```bash
dapr run --app-id pizza-kitchen --app-protocol http --app-port 8002 --dapr-http-port 3502 --resources-path ../resources  -- dotnet run
```

> [!IMPORTANT]
> If you are using Consul as a naming resolution service, add `--config ../resources/config/config.yaml` before `-- dotnet run` on your Dapr run command.

## Test the service

### Use VS Code REST Client

Open `PizzaStore.rest` and create a new order, similar to what was done on the first challenge.

Navigate to the _pizza-kitchen_ terminal, where you should see the following logs:

```zsh
== APP == Cooking order: 1393ff15-10fa-4a71-ad23-851157f9f748
== APP == Cooking done: 1393ff15-10fa-4a71-ad23-851157f9f748
== APP == Order ready for delivery: 1393ff15-10fa-4a71-ad23-851157f9f748
```

### Use _cURL_

Alternatively, open a third terminal window and create a new order via cURL:

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:8001/orders
```

## Next steps

Now that the services are updating the event information for every order step, you need to make sure that this information is being updated in the Redis state store. You will do this in the next challenge using Dapr [Pub/Sub](/docs/challenge-3/dotnet.md)!
