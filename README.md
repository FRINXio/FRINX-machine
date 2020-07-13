# FRINX-machine
The project is a containerized package of:

* [FRINX UniConfig]
* FRINX fork of Netflix's [Conductor]
* Elastic's
    * [Elasticsearch]
    * [Kibana]
    * [Logstash]
* FRINX microservices to execute conductor tasks
* Device simulation container
* [Uniconfig-ui]
* [Portainer]
* [PostgreSQL]

### Requirements
* 16GB and 4 CPU
* [Docker](https://www.docker.com/)
* [Docker Compose](https://github.com/docker/compose)
* [Manage Docker as a non-root user](https://docs.docker.com/install/linux/linux-postinstall/)
* License for FRINX UniConfig (you can find a trial license in the "Installation Guide" section below)

### Tested on
* Ubuntu 16.04 / 18.04 /
* docker 18.03.1-ce, v18.06.1-ce, 18.09.5
* docker-compose 1.21.2, v1.22.0 (we had issues with v1.25.0, please don't use this version)
* Chrome browser

#### Services used in the project
* uniconfig
* dynomite
* conductor-server
* elasticsearch
* kibana
* logstash
* micros
* uniconfig-ui
* portainer
* postgresql

## Installation Guide
#### Trial license
We offer a 30 day trial license. No signup needed! Alredy bundled in release.
License token:
```
e326aaa7b1741bb530d201c49f4311d3d0f391893e15393894a77180e6478289cd1709e4afe3a643100ccd31052430de1955540cf5ae1e510d657bd2af8ef2fc
```

30 days after your first installation, your token will expire and you will see an error message during Uniconfig startup. If you would like to continue with your evaluation, please register as a user on our homepage, where you will find another 30 day token under the section "My License Information". After the second trial period has expired, you can continue with a commercial license that has no time limitations.



#### Get the project
Download zip of release v1.1:
https://github.com/FRINXio/FRINX-machine/releases/download/v1.1/FRINX-machine_v1.1.zip

Unzip:
```bash
unzip FRINX-machine_v1.1.zip -d /path/to/unzip/to
```
Change to FRINX-machine directory:
```bash
cd /path/to/unzip/to/FRINX-machine
```

### Installation

The installation script `install.sh` is in the FRINX-machine folder.

The installation script does the following things:
* Copies license token
* Pulls conductor project parts from maven repository
* Builds conductor-server .jar file
* Pulls and creates docker images
* Creates external volumes for data persistence


We recommend to run the install script as regular user and not as sudo, so all files can be edited by the regular user later.
Installation with the trial license token:
```
./install.sh -l e326aaa7b1741bb530d201c49f4311d3d0f391893e15393894a77180e6478289cd1709e4afe3a643100ccd31052430de1955540cf5ae1e510d657bd2af8ef2fc
```
After the first run the license token is saved to a <git directory>/uniconfig/frinx.license.cfg and will be copied to image after each update.


### Startup
The startup script `startup.sh` can be found in the FRINX-machine folder.
Here is what it does:
* Creates the docker containers from the images and starts them.
* Imports workflow definitions.
* Adds sample devices to inventory
* Starts simulated devices
* Deploys bridge (default) or host networking (optional)


Info about BRIDGE networking:
https://docs.docker.com/network/bridge/

More info when to use HOST networking:
https://docs.docker.com/network/host/



Bridge networking is executed by command:

```bash
./startup.sh
```

Host networking is executed by command:

```bash
./startup.sh -n host
```


#### Web interface
Open web page:
 http://localhost:3000

Container management(portainer):
 http://localhost:9000

### Install demo workflows
After following the steps above you will have a clean installation of FRINX Machine and you can create or load your own workflows. We have created a repository of demo and sample workflows to get familiar with FRINX Machine and to have a starting point for your own work.

Go to the Frinx-machine folder and clone the following respoitory:

```bash
cd FRINX-machine/
cd ..
git clone https://github.com/FRINXio/fm-workflows.git
```
While FRINX Machine is running execute the startup script inside the fm-workflows folder
```bash
cd fm-workflows/
git checkout 8a611581b3d8b7f75e3348e4723dbf756c3ea02e #valid for downloaded FRINX-machine v1.1
./startup.sh
```
The startup script will load sample devices and sample workflows into your FRINX Machine setup.

## Documentation & Use Cases
More detailed documentation and use cases can be found at https://docs.frinx.io/FRINX_Machine/index.html.

### Teardown
The `teardown.sh` script in the FRINX-machine folder:
* Stops and removes containers
* Optionially removes volumes and images used by services in the `docker-compose.*.yml` file.

Using docker, also needs privileged mode:
```bash
./teardown.sh [-v|--volumes] [-i|--images]
```

#### **Caution all data will be lost if you use the `--volumes` flag!**


### For developers

Once images were downloaded, to update images from Docker Hub:
```
./install.sh [service]
```

To build image from cloned repository:
```
./install.sh -b [service]
```
If no container is specified all are updated.


To use latest version of submodules for locally built images:
```
./install.sh --dev -b [service]
```

To replace running service with new one run after updating the image:
```
docker stop [service]
docker rm [service]
docker-compose -f docker-compose.[networking].yml up -d [service]
```
e.g. in case of bridge networking

```bash
docker-compose -f docker-compose.bridge.yml up -d [service]
```

and in case of host networking

```bash
docker-compose -f docker-compose.host.yml up -d [service]
```

[FRINX UniConfig]: <https://frinx.io/odl_distribution>
[Conductor]: <https://github.com/FRINXio/conductor>
[Elasticsearch]: <https://www.elastic.co/products/elasticsearch>
[Kibana]: <https://www.elastic.co/products/kibana>
[Logstash]: <https://www.elastic.co/products/logstash>
[Uniconfig-ui]: <https://github.com/FRINXio/frinx-uniconfig-ui>
[Portainer]: <https://www.portainer.io/>
[PostgreSQL]: <https://hub.docker.com/_/postgres>
