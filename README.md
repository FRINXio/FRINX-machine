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



## Getting started
 
#### Installation
Go to the FRINX-machine folder and execute the `install.sh` with mandatory switch -l 
what takes the FRINX ODL license token.
* Builds conductor-server .jar file.
* Creates docker images.
* Creates external volumes for data persistence.

```bash
usage: install.sh MANDATORY 

MANDATORY:
  -l | --license  VAL     License token
```


Should be executed with sudo otherwise it will prompt for your password in the middle of the script.

```bash
cd FRINX-machine
sudo ./install.sh -l 3546840658406840664648465647486779874946564789746876854068
```


### Startup
In the FRINX-machine folder execute the `startup.sh` script.
```bash
usage: startup.sh [OPTION]  

OPTION:
  -m | --minimal   Start with minimal resource usage and frinxit disabled.
```

* Creates the docker containers from the images and starts them.
* Waits for containers to start.
* Imports workflow definitions.


Should be executed with sudo otherwise it will prompt for your password in the middle of the script.
```bash
cd FRINX-machine
sudo ./startup.sh
```

Docker expects that the external volumes exist when starting the containers.  
If they were removed, they can be created with:
```bash
sudo docker volume create --name=redis_data
sudo docker volume create --name=elastic_data
```


### Teardown
In the FRINX-machine folder execute the `teardown.sh` script.
* Stops and removes containers.
* Does not remove external volumes.

To remove the external volumes use:  
**Caution all data will be lost!**
```bash
sudo docker volume rm redis_data
sudo docker volume rm elastic_data
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