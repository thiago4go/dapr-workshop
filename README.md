# Dapr Workshop

## Overview & Goals

Welcome to Diagrid's [Dapr](https://dapr.io/) Workshop! Our goal is for you to familiarize with Dapr's most popular APIs and give you a starting point so you can start building your own distributed applications right away!

Microservices are popular for multiple reasons. They can be written in any programming language and can be small enough to perform simple and easy to execute tasks. Because of that, your solution can end up with hundreds of them, all over the place. And this where all the problems begin. Security, observability, resiliency become challenges that are no easy to overcome, and that's where Dapr comes in.

## Path

### State Store

We will start the workshop by creating a new order and saving it to Redis, using the State Store API. You will learn how to create a component definiton fine, and how to use the Dapr SDK to save and to retrieve an item from Redis.

### Service Invocation

Now that you learned the basics, let's jump to another popular API: Service Invocation. After the order is saved, we will create another service that is responsible for cooking the pizza for us.

### Pub/Sub

Then, we will learn how to leverage Dapr's Pub/Sub API to publish events to Redis from ordering the pizza, to cookign and delivering it. We will also subscribe to these events and updating them in the UI.

## Getting started

In order to partake in the workshop, you will be required to install the following [technical prerequisites](./docs/prerequisites.md).
