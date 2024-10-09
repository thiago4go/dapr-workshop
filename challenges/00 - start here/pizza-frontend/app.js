// Dapr configuration
const DAPR_HTTP_PORT = 3506; // Default Dapr HTTP port
const PUBSUB_NAME = 'pizzapubsub';
const TOPIC_NAME = 'order';

var currentEvent = "";
var currentOrder = "";

function connect() {
    console.log("Connected to Dapr sidecar");
    setConnected(true);
    //subscribeToEvents();
}

function subscribeToEvents() {
    // In a real application, you would set up server-sent events or long-polling here
    // For simplicity, we'll just poll for new events every 5 seconds
    setInterval(fetchEvents, 1000);
}

function fetchEvents() {
    if (currentOrder != ""){
        if (currentEvent != "Delivered") {
            fetch("http://127.0.0.1:8001/orders/" + currentOrder, {
                method: 'GET',
            })
            .then(response => response.json())
            .then(event => {
                event = event.replace(/'/g, '"')
                showEvent(event);
            })
            .catch(error => console.error('Error fetching events:', error));
        }
    } 
}

function setConnected(connected) {
    $("#connect").prop("disabled", connected);
    $("#disconnect").prop("disabled", !connected);
    if (connected) {
        $("#conversation").show();
    }
    else {
        $("#conversation").hide();
    }
    $("#events").html("");
}

function placeOrder() {
    $("#events").empty();
    $("#status").empty();

    currentEvent = "";
    currentOrder = "";

    console.log("Placing Order");

    const order = {
        customer: {
            name: $("#customerName").val(),
            email: $("#customerEmail").val(),
        },
        items: [
            {
                "type": $("#pizzaType").val(),
                "amount": 1,
            }
        ],
        address: $("#address").val(),
        creditCard: $("#creditCard").val(),
        drink: $("#drink").val()
    };

    console.log("Order placed successfully");

    fetch("http://127.0.0.1:8001/orders", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(order),
    })
    .then(response => response.json())
    .then(response => {
        console.log("jsonObj: ", response.orderId);
        currentOrder = response.orderId;
        subscribeToEvents();
    })
    .catch(error => console.error('Error:', error));
}

function disconnect() {
    setConnected(false);
    console.log("Disconnected");
}

function createItem(detailsImage, text, disabled) {
    var item = "<div class='item animate'>" +
        "<div class='green-dot'>";
    if (disabled) {
        item += "<img class='disabled transition' src='imgs/GreenDot.png'/>";
    } else {
        item += "<img class='transition' src='imgs/GreenDot.png'/>";
    }
    item += "</div>" +
        "<div class='details'>" +
        "<img src='imgs/" + detailsImage + "'/>" +
        "<p>" + text + "</p>" +
        "</div>" +
        "</div>";
    return item;
}

function createEventEntry(event) {

    var eventEntry = "<div>" +
        "<p>Pizza for <strong>" + event.customer.name + "</strong></p>" +
        "<p>Event Type: <strong>" + event.event + "</strong></p>" +
        "<p>Pizza: <strong>" + event.items[0].type + "</strong></p>" +
        "</div>";
    return eventEntry;

}

function showEvent(event) {
    var eventObj = JSON.parse(event);
    if (currentEvent === eventObj.event) {
        return;
    }

    $("#events").prepend(createEventEntry(eventObj));
    
    currentEvent = eventObj.event;

    $("#status").empty();

    if (eventObj.event === "Sent to kitchen") {
        $("#status").append(createItem("Order.png", "Order Placed", false));
    }
    if (eventObj.event === "Cooking") {
        $("#status").append(createItem("PizzaInOven.png", "Your Order is being prepared.", false));
    }
    
    if (eventObj.event === "Ready for delivery" 
        || eventObj.event === "Order picked up by driver" ) {
        $("#status").append(createItem("Delivery.png", eventObj.event, false));
    }

    if (eventObj.event === "Delivery started" 
        || eventObj.event === "En-route" 
        || eventObj.event === "Nearby") {

        $("#status").append(createItem("Map.gif", eventObj.event, false));
    }
    if (eventObj.event === "Delivered") {
        $("#status").append(createItem("BoxAndDrink.png", "Your order is now complete. Thanks for choosing us!", false));
    }

}
$(function () {
    $("form").on('submit', (e) => e.preventDefault());
    $("#connect").click(() => connect());
    $("#disconnect").click(() => disconnect());
    $("#placeOrder").click(() => placeOrder());
});