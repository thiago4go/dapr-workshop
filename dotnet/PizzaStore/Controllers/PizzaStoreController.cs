using Microsoft.AspNetCore.Mvc;
using Dapr.Client;
using System.Text.Json;


namespace PizzaStore.Controllers;

[ApiController]
[Route("[controller]")]
public class PizzaStoreController : ControllerBase
{
    private readonly string StateStoreName = "pizzastatestore";
    private readonly string PubSubName = "pizzapubsub";
    private readonly string TopicName = "order";

    private readonly ILogger<PizzaStoreController> _logger;

    public PizzaStoreController(ILogger<PizzaStoreController> logger)
    {
        _logger = logger;
    }

    // -------- Dapr State Store -------- //

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

    // -------- Dapr Pub/Sub -------- //

    [HttpPost("/events")]
    public async Task<IActionResult> Process([FromBody] JsonDocument rawTransaction)
    {
        Console.WriteLine("Processing order: " + JsonSerializer.Serialize(rawTransaction));

        var order = JsonSerializer.Deserialize<Order>(rawTransaction.RootElement.GetProperty("data").GetRawText());

        if (order is null)
        {
            return BadRequest();
        }

        await SaveOrderToStateStore(order);

        // check if event is sent to kitchen
        if (order.Event == "Sent to kitchen")
        {
            await Task.Delay(4000);
            // Start cooking
        }

        if (order.Event == "Ready for delivery")
        {
            //start delivery
        }

        return Ok();
    }

    // -------- Application routes -------- //

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

        Console.WriteLine("Posting order: " + order.Address);

        // publish the order
        var client = new DaprClientBuilder().Build();

        // create metadata
        var metadata = new Dictionary<string, string> { { "Content-Type", "application/json" } };
        await client.PublishEventAsync(PubSubName, TopicName, order, metadata, cancellationToken: CancellationToken.None);

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

}


// dapr run --app-id pizza-store --app-protocol http --app-port 5294 --dapr-http-port 3500 --resources-path ../resources  -- dotnet run
