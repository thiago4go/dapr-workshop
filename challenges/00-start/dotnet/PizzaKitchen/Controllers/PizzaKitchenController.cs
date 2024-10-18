using Microsoft.AspNetCore.Mvc;
using Dapr.Client;
using System.Text.Json;

namespace PizzaKitchen.Controllers;

[ApiController]
[Route("[controller]")]
public class PizzaKitchenController : ControllerBase
{
    private readonly ILogger<PizzaKitchenController> _logger;

    public PizzaKitchenController(ILogger<PizzaKitchenController> logger)
    {
        _logger = logger;
    }

    // -------- Dapr Pub/Sub -------- //

    // -------- Application routes -------- //


}

