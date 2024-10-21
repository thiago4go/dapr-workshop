using Microsoft.AspNetCore.Mvc;
using Dapr.Client;

namespace PizzaKitchen.Controllers;

[ApiController]
[Route("[controller]")]
public class PizzaKitchenController : ControllerBase
{
    private readonly string PubSubName = "pizzapubsub";
    private readonly string TopicName = "order";

    private readonly ILogger<PizzaKitchenController> _logger;

    public PizzaKitchenController(ILogger<PizzaKitchenController> logger)
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

}


