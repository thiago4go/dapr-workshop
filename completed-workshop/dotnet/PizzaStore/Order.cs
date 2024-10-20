using System.Text.Json.Serialization;

namespace PizzaStore;

public class Customer
{

    [JsonPropertyName("email")]
    public string? Email { get; set; }

    [JsonPropertyName("name")]
    public string? Name { get; set; }
}

public class Item
{
    [JsonPropertyName("amount")]
    public int Amount { get; set; }

    [JsonPropertyName("type")]
    public string? Type { get; set; }
}

public class Order
{
    [JsonPropertyName("address")]
    public string? Address { get; set; }

    [JsonPropertyName("creditCard")]
    public string? CreditCard { get; set; }

    [JsonPropertyName("customer")]
    public Customer? Customer { get; set; }

    [JsonPropertyName("drink")]
    public string? Drink { get; set; }

    [JsonPropertyName("event")]
    public string? @Event { get; set; }

    [JsonPropertyName("items")]
    public List<Item>? Items { get; set; }

    [JsonPropertyName("order_id")]
    public string? OrderId { get; set; }
}

