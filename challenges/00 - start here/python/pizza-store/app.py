from flask import Flask
from flask_cors import CORS
from dapr.clients import DaprClient

import uuid
import logging
import json

DAPR_PORT = 8001

logging.basicConfig(level=logging.WARN)

app = Flask(__name__)
CORS(app)

# ------------------- Dapr State Store ------------------- #

# ------------------- Dapr Service Invocation ------------------- #

# ------------------- Dapr Pub/Sub ------------------- #

# ------------------- Application routes ------------------- #

app.run(port=8001)