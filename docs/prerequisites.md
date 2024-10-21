# Prerequisites

## Download and install the following dependencies

- [Docker](https://docs.docker.com/engine/install/)
- [Visual Studio Code](https://code.visualstudio.com/download)
- [REST Client for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
- [Redis Insights](https://redis.io/insight/) Optional: to visualize the data on Redis.
- [Powershell(for Windows users)](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.4)

<details>

<summary>Python</summary>

- [Python 3](https://www.python.org/downloads/)
- [Python Extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

</details>

<details>

<summary>dotnet</summary>

- [dotnet 8.0](https://dotnet.microsoft.com/download/dotnet/8.0)
- [C# Extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.csharp)

</details>

## Install Dapr

1. Follow [these steps](https://docs.dapr.io/getting-started/install-dapr-cli/) to install the Dapr CLI.

2. [Initialize Dapr](https://docs.dapr.io/getting-started/install-dapr-cli/):

```bash
dapr init
```

3. Verify if local containers are running:

```bash
docker ps
```

![containers](./../imgs/docker-ps.png)

## Some considerations

### Integrated terminal 

During the workshop, you should be working in 1 instance of VS Code. You will use the integrated terminal in VS Code extensively. All terminal commands have been tested on a Apple M3 Pro using an integrated terminal.

### Prevent port collisions

During the workshop you will run the services in the solution on your local machine. To prevent port-collisions, all services listen on a different HTTP port. When running the services with Dapr, you need additional ports for HTTP and gRPC communication with the sidecars. If you follow the instructions, the services will use the following ports for their Dapr sidecars to prevent port collisions:

| Service                    | Application Port | Dapr sidecar HTTP port  |
|----------------------------|------------------|------------------------|
| pizza-store      | 6000             | 3501                   |
| pizza-kitchen      | 6001             | 3502                  |
| pizza-delivery | 6002             | 3503               |

If you're on Windows with Hyper-V enabled, you might run into an issue that you're not able to use one (or more) of these ports. This could have something to do with aggressive port reservations by Hyper-V. You can check whether or not this is the case by executing this command:

```powershell
netsh int ipv4 show excludedportrange protocol=tcp
```

If you see one (or more) of the ports shown as reserved in the output, fix it by executing the following commands in an administrative terminal:

```powershell
dism.exe /Online /Disable-Feature:Microsoft-Hyper-V
netsh int ipv4 add excludedportrange protocol=tcp startport=6000 numberofports=3
netsh int ipv4 add excludedportrange protocol=tcp startport=3501 numberofports=3
dism.exe /Online /Enable-Feature:Microsoft-Hyper-V /All
```

### Running self-hosted on MacOS with Antivirus software

Some antivirus software blocks mDNS (we've actually encountered this with Sophos). mDNS is used for name-resolution by Dapr when running in self-hosted mode. Blocking mDNS will cause issues with service invocation. When you encounter any errors when invoking services using service invocation, use Consul as an alternative name resolution service.

Run the following command line to initialize Consul:

```bash
docker run -d -p 8500:8500 -p 8600:8600/udp --name dtc-consul consul:1.15 agent -dev -client '0.0.0.0'
```

Then, when you finish all challenges, run:

```bash
docker rm dtc-consul -f
```

You can verify whether Consul is used for name-resolution by searching for the occurrence of the following line in the Dapr logging:

```bash
ℹ️  Starting Dapr with id pizza-kitchen. HTTP Port: 3502.
...
INFO[0000] Initialized name resolution to consul ...
...
```

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
