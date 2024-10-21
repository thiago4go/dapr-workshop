# Prerequisites

## Download and install the following dependencies

- [Docker](https://docs.docker.com/engine/install/)
- [Visual Studio Code](https://code.visualstudio.com/download)
- [REST Client for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
- [Redis Insights](https://redis.io/insight/) Optional: to visualize the data on Redis.

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

### Instructions

Every assignment is contained in a separate folder in this repo. Each folder contains the description of the assignment that you can follow.

**It is important you work through all the assignments in order and don't skip any assignments. The instructions for each assignment rely on the fact that you have finished the previous assignments successfully.**

You will be provided with a starting point for the workshop. This starting point is a working version of application in which the services use plain HTTP to communicate with each-other and state is stored in memory. With each assignment of the workshop, you will add a Dapr building block to the solution.

Every assignment offers instructions on how to complete the assignment. With the exception of assignment 1, each assignment offers two versions of the instructions: the **DIY** version and the **step-by-step** version. The DIY version just states the outcome you need to achieve and no further instructions. It's entirely up to you to achieve the goals with the help of the Dapr documentation. The step-by-step version describes exactly what you need to change in the application step-by-step. It's up to you to pick an approach. If you pick the DIY approach and get stuck, you can always go to the step-by-step instructions for some help.

#### Integrated terminal

During the workshop, you should be working in 1 instance of VS Code. You will use the integrated terminal in VS Code extensively. All terminal commands have been tested on a Windows machine with the integrated Powershell terminal in VS Code. If you have any issues with the commands on Linux or Mac, please create an issue or a PR to add the appropriate command.

#### Prevent port collisions

During the workshop you will run the services in the solution on your local machine. To prevent port-collisions, all services listen on a different HTTP port. When running the services with Dapr, you need additional ports for HTTP and gRPC communication with the sidecars. By default these ports are `3501` and `50001`. But to prevent confusion, you'll use totally different port numbers in the assignments. If you follow the instructions, the services will use the following ports for their Dapr sidecars to prevent port collisions:

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

#### Running self-hosted on MacOS with Antivirus software

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
ℹ️  Starting Dapr with id vehicleregistrationservice. HTTP Port: 3602. gRPC Port: 60002
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
