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
    private readonly DaprClient _daprClient;

    public PizzaStoreController(DaprClient daprClient, ILogger<PizzaStoreController> logger)
    {
        _logger = logger;
        _daprClient = daprClient;
    }

    // -------- Dapr State Store -------- //

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

    // -------- Dapr Pub/Sub -------- //
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

    // -------- Dapr Service Invocation -------- //
    private async Task Cook(Order order)
    {
        var client = DaprClient.CreateInvokeHttpClient(appId: "pizza-kitchen");

        var response = await client.PostAsJsonAsync("/cook", order, cancellationToken: CancellationToken.None);
        Console.WriteLine("Returned: " + response.StatusCode);
    }

    private async Task Deliver(Order order)
    {
        var client = DaprClient.CreateInvokeHttpClient(appId: "pizza-delivery");

        // To set a timeout on the HTTP client:
        //client.Timeout = TimeSpan.FromSeconds(2);

        var response = await client.PostAsJsonAsync("/deliver", order, cancellationToken: CancellationToken.None);
        Console.WriteLine("Returned: " + response.StatusCode);
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
        order.Event = "Sent to kitchen";

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


