# FRINX-machine
The project is a containerized package of: 

* [FRINX ODL]
* FRINX fork of Netflix's [Conductor]
* Elastic's
    * [Elasticsearch]
    * [Kibana]
    * [Logstash]
* FRINX microservices to execute conductor tasks
* Device simulation container
* [Uniconfig-ui]


## Requirements
* 16GB and 4 CPU
* [Docker](https://www.docker.com/)
* [Docker Compose](https://github.com/docker/compose)
* License for FRINX ODL (you can find a trial license in the "Installation Guide" section below)

### Tested on
* Ubuntu 16.04 / 18.04 /
* docker 18.03.1-ce, v18.06.1-ce, 18.09.5
* docker-compose 1.21.2, v1.22.0
* Chrome browser


## Installation Guide
#### Trial license
We offer a 30 day trial license. No signup needed!
License token:
```
e326aaa7b1741bb530d201c49f4311d3d0f391893e15393894a77180e6478289cd1709e4afe3a643100ccd31052430de1955540cf5ae1e510d657bd2af8ef2fc
```

30 days after your first installation, your token will expire and you will see an error message during ODL startup. If you would like to continue with your evaluation, please register as a user on our homepage, where you will find another 30 day token under the section "My License Information". After the second trial period has expired, you can continue with a commercial license that has no time limitations. 

#### Get the project
Clone the repository:
```bash
git clone -b 0.9 https://github.com/FRINXio/FRINX-machine.git
```
Navigate into the project folder:
```bash
cd FRINX-machine
```

#### Services used in the project
* odl
* conductor-server
* elasticsearch
* kibana
* logstash
* micros
* uniconfig-ui
* sample-topology
 
### Installation

The installation script `install.sh` is in the FRINX-machine folder. 

The installation script does the following things:
* Updates project submodules (e.g. conductor)
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
After the first run the license token is saved to a <git directory>/odl/frinx.license.cfg and will be copied to image after each update.


### Startup
The startup script `startup.sh` can be found in the FRINX-machine folder.
Here is what it does:
* Creates the docker containers from the images and starts them.
* Imports workflow definitions.
* Adds sample devices to inventory
* Starts simulated devices


Docker needs privileged mode, so `startup.sh` should be executed with sudo. Otherwise it will prompt for password while executing.
```bash
sudo ./startup.sh
```

#### Web interface
Open web page:
 http://localhost:3000

## Documentation & Use Cases
More detailed documentation and use cases can be found at https://docs.frinx.io/FRINX_Machine/index.html.

### Teardown
The `teardown.sh` script in the FRINX-machine folder:
* Stops and removes containers
* Does not remove external volumes

Using docker, also needs privileged mode:
```bash
sudo ./teardown.sh
```

### Removal of external volumes
#### **Caution all data will be lost!**

To remove the volumes use:
```bash
sudo docker volume rm redis_data elastic_data odl_logs
```

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

To replace running service with new one run after updating the image:
```
sudo docker stop [service]
sudo docker rm [service]
sudo docker-compose up -d [service]
```

[FRINX ODL]: <https://frinx.io/odl_distribution>
[Conductor]: <https://github.com/FRINXio/conductor>
[Elasticsearch]: <https://www.elastic.co/products/elasticsearch>
[Kibana]: <https://www.elastic.co/products/kibana>
[Logstash]: <https://www.elastic.co/products/logstash>
[Uniconfig-ui]: <https://github.com/FRINXio/frinx-uniconfig-ui>
