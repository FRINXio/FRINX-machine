# FRINX-machine
The project is a dockerized package of: 

* [FRINX ODL]
* fork of [Conductor]
* Elastic's
    * [Elasticsearch]
    * [Kibana]
    * [Logstash]
* Microservices engine
* [frinxit]



## Requirements
* [Docker](https://www.docker.com/)
* [Docker Compose](https://github.com/docker/compose)
* JDK 1.8
* License for FRINX ODL

min 16GB RAM & min 4 vCPUs with normal startup, and 5GB RAM & 2 vCPUs with minimal config should be enough. 

### Tested on
* Ubuntu 16.04 / 18.04
* docker 18.03.1-ce, v18.06.1-ce 
* docker-compose 1.21.2, v1.22.0



## Getting started
##### Trial license
We offer a one month trial license. No signup needed!
License token:
```
0e57a786f7dbd27fa77db684cf3b234d6f23ed784e52cbfb107fd4317ba2646c66f7a141b0e823946d8f9d956852c95d33dc82f945779b1c9969049e94935b2a
```

#### Get the project
Clone the repository:
```bash
git clone https://github.com/FRINXio/FRINX-machine.git
```
Navigate into the project folder:
```bash
cd FRINX-machine
```

 
#### Installation
The installation script `install.sh` is in the FRINX-machine folder. 
What does installation do:
* Updates project submodules
* Copies license token. 
* Pulls conductor project parts from maven repository.
* Builds conductor-server .jar file.
* Pulls and creates docker images.
* Creates external volumes for data persistence.


Docker needs privileged mode, so `install.sh` should be executed with sudo. Otherwise it will prompt for password while executing.

Installation with the trial license token:
```
sudo ./install.sh -l 0e57a786f7dbd27fa77db684cf3b234d6f23ed784e52cbfb107fd4317ba2646c66f7a141b0e823946d8f9d956852c95d33dc82f945779b1c9969049e94935b2a
```

#### Startup
The startup script `startup.sh` can be found in the FRINX-machine folder.
What does it do:
* Creates the docker containers from the images and starts them.
* Imports workflow definitions.


Docker needs privileged mode, so `startup.sh` should be executed with sudo. Otherwise it will prompt for password while executing.
```bash
sudo ./startup.sh
```
Min 16GB RAM & min 4 vCPUs with normal startup are recommended.

##### Minimal startup
```bash
sudo ./startup.sh -m
```
Starts application with lower RAM usage. Min 5GB RAM & min 2 vCPUs with minimal startup are recommended.

#### Teardown
The `teardown.sh` script in the FRINX-machine folder:
* Stops and removes containers.
* Does not remove external volumes.

Using docker, also needs privileged mode:
```bash
sudo ./teardown
```

## Removal of external volumes
#### **Caution all data will be lost!**

To remove the external volumes use:
```bash
sudo docker volume rm redis_data elastic_data
```
Docker expects external volumes to exist when starting the containers.
They can be created with:
```bash
sudo docker volume create --name=redis_data
sudo docker volume create --name=elastic_data
```

### Exposed ports
* Conductor-server: 
	* host:8080
	* host:8000

* Conductor-ui: 
	* host:5000

* ODL: 
	* host:8181

* Frinxit: 
	* host:8888

* Microservices: 
	* host:6000

* Elasticsearch: 
	* host:9200
	* host:9300
* Kibana:
    * host:5601



[FRINX ODL]: <https://frinx.io/odl_distribution>
[Conductor]: <https://github.com/FRINXio/conductor>
[frinxit]: <https://github.com/FRINXio/frinxit>
[Elasticsearch]: <https://www.elastic.co/products/elasticsearch>
[Kibana]: <https://www.elastic.co/products/kibana>
[Logstash]: <https://www.elastic.co/products/logstash>
