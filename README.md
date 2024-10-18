# Dapr Workshop


## Overview

Welcome to Diagrid's [Dapr](https://dapr.io/) Workshop! Our goal is for you to familiarize with Dapr's most popular APIs and give you a starting point so you can start building your own distributed applications right away!

Microservices are popular for multiple reasons. They can be written in any programming language and can be small enough to perform simple and easy to execute tasks. Because of that, your solution can end up with hundreds of them, all over the place. And this where all the problems begin: security, observability, resiliency become challenges that are no easy to overcome, and that's where Dapr comes in.

## Goals

Our goal for this workshop is to understand how 3 of the most popular Dapr Building Blocks work: [State Management](https://docs.dapr.io/developing-applications/building-blocks/state-management/), [Service Invocation](https://docs.dapr.io/developing-applications/building-blocks/service-invocation/), and [Publish/Subscribe](https://docs.dapr.io/developing-applications/building-blocks/pubsub/).

We are going to create 3 services to manage simulate the process of ordering a pizza:

- `pizza-store` orchestrates the whole process: ordering the pizza, cooking, and delivering.
- `pizza-kitchen` has a single responsibility: cooking the pizza.
- `pizza delivery` manages the whole delivery process: from picking up the pizza at the kitchen all the way up to delivering it to the customer's doorstep.

## Challenge path

### Challenge 1 - State Store

We will start the workshop by creating a new order and saving it to Redis, using the State Store API. You will learn how to create a component definiton fine, and how to use the Dapr SDK to save and to retrieve an item from Redis.

![challenge-1](/imgs/challenge-1.png)

### Challenge 2 - Service Invocation

Now that you learned the basics, let's jump to another popular API: Service Invocation. After the order is saved, we will create another service that is responsible for cooking the pizza for us.

![challenge-2](/imgs/challenge-2.png)

### Challenge 3 - Pub/Sub

Then, we will learn how to leverage Dapr's Pub/Sub API to publish events to Redis from ordering the pizza, to cooking and delivering it. We will also subscribe to these events and updating them in the UI.

![challenge-3](/imgs/challenge-3.png)

## Getting started

In order to partake in the workshop, you will be required to install the following [technical prerequisites](./docs/prerequisites.md).