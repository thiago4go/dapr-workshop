# Python

## Clone the repository and initialize the environment

On your terminal, run:

```bach
git clone https://github.com/diagridlabs/dapr-workshop
cd dapr-worksop
```

Navigate to the starting point:

```bash
cd start-here
```

Install vevn:

```bash
pip install virtualenv
```

Initialize the virtual environment:

```bash
python -m venv env
source env/bin/activate
```

## Challenge 1 - State Store

### Overview

In our first challenge, we will create a new service called _pizza-store_. We will configure a new Redis state store to save, get, and delete an order.

### Configuring the state store

Navigate to the `/resources` folder and create a new file called `statestore.yaml`. Add the content below to the file:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pizzastatestore
spec:
  type: state.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
  - name: redisPassword
    value: ""
```

This is a component definition file named `pizzastatestore`. In the _spec_ definition, note that the type of the component is `state_redis` and the metadata contains host and password information for our Redis instance that was deployed as a container during Dapr's initialization. process.

### Installing the dependencies

Now navigate to `python/pizza-store`. This folder contains the `app.py` file which contains our application. Before start coding, let's install our dependencies.

Let's start by creating a new file called `requirements.txt`. This file will hold our dependencies. Add the content below to it:

```text
Flask
flask-cors
dapr
uvicorn
typing-extensions
```

Run the command below to install the dependencies:

```bash
pip install -r pizza-store/requirements.txt
```

### Creating the service

1. Open `app.py`. Notice the two import lines, let's add a couple more libraries there:

```python
from flask import Flask, request
from flask_cors import CORS
from dapr.clients import DaprClient

import uuid
import logging
import json
```

We are now importing DaprClient from dapr.clients. That's what we will use to manage the state in our Redis instance.

2. 
