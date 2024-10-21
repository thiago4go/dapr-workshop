## Challenge 2 - Service Invocation

### Overview

On our second challenge, we will send the order created in the previous step to the kitchen! For that, we will:

- Create a new service called _pizza-kitchen_ with a `/cook` endpoint.
- Update _pizza-store_ to invoke the `/cook` endpoint with the Service Invocation building block.

To learn more about the Service Invocation building block, refer to the [Dapr docs](https://docs.dapr.io/developing-applications/building-blocks/service-invocation/).

### Installing the dependencies

Navigate to `/PizzaKitchen`. Before start coding, let's install our Dapr dependencies.

```bash
cd PizzaKitchen
dotnet add package Dapr.Client
```

### Creating the service

Open `/Controllers/PizzaKitchenController.cs` Let's add a couple of import statements.

```csharp
using Microsoft.AspNetCore.Mvc;
using Dapr.Client;
```

### Creating the app route

Leet's create our route that will tell the kitchen to start cooking the pizza `/cook`. Below **# Application routes #** add the following:

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

This route is fairly simple. It is a POST request with the `order` content created in the last challenge. We will start the order and, after it is cooked, we will say it is ready.

Add two helper functions to modify the order to _Cooking_ and to _Ready for delivery_.

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

#### Calling the app route

Let's go back to the _pizza-store_ service. We will create a Service Invocation action to call the `/cook` endpoint from our _pizza-kitchen_ service.

First, update the `PostOrder()` function, add the following line after the `await SaveOrderToStateStore(order);` invocation:

```csharp
// Start cooking
await Cook(order);
```

Now, under **# Dapr Service Invocation #**, add the code below:

```csharp
private async Task Cook(Order order)
{
    var client = DaprClient.CreateInvokeHttpClient(appId: "pizza-kitchen");

    var response = await client.PostAsJsonAsync("/cook", order, cancellationToken: CancellationToken.None);
    Console.WriteLine("Returned: " + response.StatusCode);
}
```

Let's break down the code above.

1. First are using the `DaprClient` to create an HttpClient Invocation object with the app id of the service we want to invoke:

```csharp
var client = DaprClient.CreateInvokeHttpClient(appId: "pizza-kitchen");
```

The code above wraps an http call to the host `localhost` with the port `3501`. This is not calling the _pizza-kitchen_ service directly, but the sidecar of the _pizza-store_ service. The responsiblity of making the service invocation is passed to the sidecar, as the picture below illustrates:

![service-invocation](/imgs/service-invocation.png)

2. Then, we make the call to the endpoint `/cook`, passing our _order_ as the body of the POST request:

```csharp
var response = await client.PostAsJsonAsync("/cook", order, cancellationToken: CancellationToken.None);
```

With this, services only need to communicate to sidecars through localhost and the sidecar handles the discovery capabilities.

#### Running the application

We now need to run both applications. If the _pizza-store_ service is still running, press **CTRL+C** to stop it. In your terminal, navigate to the folder where the _pizza-store_ `app.py` is located and run the command below:

```bash
dapr run --app-id pizza-store --app-protocol http --app-port 8001 --dapr-http-port 3501 --resources-path ../resources  -- dotnet run
```

Open a new terminal window and mode to the _pizza-kitchen_ folder. Run the command below:

```bash
dapr run --app-id pizza-kitchen --app-protocol http --app-port 8002 --dapr-http-port 3502 --resources-path ../resources  -- dotnet run
```

> [!IMPORTANT]
> If you are using Consul as a naming resolution service, add `--config ../resources/config/config.yaml` before `-- dotnet run` on your Dapr run command.

#### Testing the service

Open `PizzaStore.rest` and create a new order, similar to what was done on ourfirst challenge.

Navigate to the _pizza-kitchen_ terminal, you should see the following logs pop up:

```zsh
== APP == Cooking order: 1393ff15-10fa-4a71-ad23-851157f9f748
== APP == Cooking done: 1393ff15-10fa-4a71-ad23-851157f9f748
== APP == Order ready for delivery: 1393ff15-10fa-4a71-ad23-851157f9f748
```

Alternatively, open a third terminal window and create a new order:

```bash
curl -H 'Content-Type: application/json' \
    -d '{ "customer": { "name": "fernando", "email": "fernando@email.com" }, "items": [ { "type":"vegetarian", "amount": 2 } ] }' \
    -X POST \
    http://localhost:8001/orders
```