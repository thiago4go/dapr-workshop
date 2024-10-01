# Dapr Workshop

## Overview & Goals

Welcome to Diagrid's [Dapr](https://dapr.io/) Workshop! Our goal is for you to familiarize with Dapr's most popular APIs and give you a starting point so you can start building your own distributed applications right away!

Microservices are popular for multiple reasons. They can be written in any programming language and can be small enough to perform simple and easy to execute tasks. Because of that, your solution can end up with hundreds of them, all over the place. And this where all the problems begin. Security, observability, resiliency become challenges that are no easy to overcome, and that's where Dapr comes in.

\
At the end of this workshop **you will**:

* Understand what Dapr is end how it can expedite your 

* A series of hands-on challenges that allow participants to implement solutions to the problems commonly faced in microservice development

* A solution that, when completed, provides a set of industry best practices to follow when building distributed systems

\
This workshop is **not**:

* An introduction into microservices or containers

* A Kubernetes workshop 

* An opportunity to learn new programming languages


## Target Audience

This workshop was created for software developers who are looking to gain a deeper understanding of how to build cloud native, distributed applications. Ideally, those looking to participate will have previous hands-on experience with microservice-based applications, however knowledge of the architectural style may also be sufficient.

Experience with the following is required:

* Azure Cloud
* Kubernetes-hosted, containerized applications (any distribution, AKS recommended)
* Software Development with one or more programming languages 

Experience with the following is recommended:

* .Net Core, NodeJS, Java or Golang programming languages 

## Learning Objectives

Over the period of approximately two days, participants will use a variety of Dapr components to build out and deploy a complete system of microservices that will replace Cloud Coffee Company's core Ordering Platform. The Dapr learning objectives that will be covered are as follows:

| Objective      | Description                                                                                |
|------------------|-------------------------------------------------------------------------------------------------------------|
| Dapr Local Development | Get Dapr running locally and set-up a local development environment. |
| Pub-sub | Use a Dapr pub-sub component to publish orders to three different subscribers.     |
| State & Secret Management   | Use Dapr State and Secret building block APIs to store and access data. |
| Service-to-service Invocation | Implement an input binding and service-to-service invocation calls between microservices.  |
| Distributed Tracing | Configure and view end-to-end tracing across Dapr components. |
| Output Bindings | Construct storage and SignalR output bindings. |
| Dapr on K8s | Configure and deploy microservices application and all Dapr components onto AKS. |

## Challenge Path

The diagram below is a depiction of the workshop journey and an overview of the Dapr concepts that will be covered along the way. 

**NOTE:** Challenge 6 is optional, as it does not provide an introduction to any new Dapr concepts, but rather improves the UI. Challenge 7 is a multi-part challenge as it deals with the operationalization of Dapr projects as a whole in Kubernetes.

\
![Challenge Path](challenges/images/challenge-path.png)

## Prerequisites

In order to partake in the workshop, you will be required to install the following [technical prerequisites](./prerequisites.md). In order to understand more about the customer backstory, check out the [customer story](customer-story.md)...



python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
