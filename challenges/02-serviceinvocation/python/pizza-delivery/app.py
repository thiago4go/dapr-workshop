from flask import Flask
import logging

DAPR_PORT = 8003

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ------------------- Dapr pub/sub ------------------- #

# ------------------- Application routes ------------------- #


app.run(port=8003)