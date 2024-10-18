# Prerequisites

## Download and install the following dependencies

- [Docker](https://docs.docker.com/engine/install/)
- [Visual Studio Code](https://code.visualstudio.com/download)

If you choose Python:

- [Python 3](https://www.python.org/downloads/)
- [Python Extension for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

If you choose dotnet:

- [dotnet 8.0](https://dotnet.microsoft.com/download/dotnet/8.0)
- [C# Extension for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.csharp)

Optional: 

- [Redis Insights](https://redis.io/insight/) Optional: to visualize the data on Redis.

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

![containers](./../imgs/docker-ps.png)

## Let's get to coding

Pick your programming language:

- [Python](/docs/challenge-1/python.md)
- [dotnet](/docs/challenge-1/dotnet.md)
