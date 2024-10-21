using Microsoft.AspNetCore.Mvc;
using Dapr.Client;

namespace PizzaDelivery.Controllers;

[ApiController]
[Route("[controller]")]
public class PizzaDeliveryController : ControllerBase
{
    private readonly string PubSubName = "pizzapubsub";
    private readonly string TopicName = "order";

    private readonly ILogger<PizzaDeliveryController> _logger;

    public PizzaDeliveryController(ILogger<PizzaDeliveryController> logger)
    {
        _logger = logger;
    }

    // -------- Dapr Pub/Sub -------- //

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

    // -------- Application routes -------- //

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
}


// dapr run --app-id pizza-delivery --app-protocol http --app-port 5058 --dapr-http-port 3503 --resources-path ../resources  -- dotnet run
