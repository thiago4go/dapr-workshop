# Prerequisites

## Download and install the following dependencies

- [Docker](https://docs.docker.com/engine/install/)
- [Python 3](https://www.python.org/downloads/)
- [Visual Studio Code](https://code.visualstudio.com/download) or your preferred IDE

## Install Dapr

1 - Follow [these steps](https://docs.dapr.io/getting-started/install-dapr-cli/) to install the Dapr CLI.
2 - [Initialize Dapr](https://docs.dapr.io/getting-started/install-dapr-cli/):

```bash
dapr init
```

3 - Verify is local containers are running:

```bash
docker ps
```

![containers](imgs/docker-ps.png)

