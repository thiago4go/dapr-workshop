# Prerequisites

## Download and install the following dependencies

- [Docker](https://docs.docker.com/engine/install/)
- [Visual Studio Code](https://code.visualstudio.com/download)
- [Redis Insights](https://redis.io/insight/) Optional: to visualize the data on Redis.

<details>

<summary>Python</summary>

- [Python 3](https://www.python.org/downloads/)
- [Python Extension for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

</details>

<details>

<summary>dotnet</summary>

- [dotnet 8.0](https://dotnet.microsoft.com/download/dotnet/8.0)
- [C# Extension for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.csharp)

</details>

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

### Clone the repository and initialize the environment

<details>
  
<summary>Python</summary>

On your terminal, run:

```bash
git clone https://github.com/diagrid-labs/dapr-workshop-python.git
cd dapr-worksop-python
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

</details>

<details>
  
<summary>dotnet</summary>

On your terminal, run:

```bash
git clone https://github.com/diagrid-labs/dapr-workshop-csharp.git
cd dapr-worksop-csharp
```

</details>

### Start the first challenge

Pick your programming language:

- [Python](/docs/challenge-1/python.md)
- [dotnet](/docs/challenge-1/dotnet.md)
