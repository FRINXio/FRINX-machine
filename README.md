# FRINX-machine
The project is a dockerized package of [FRINX ODL], fork of [Conductor], microservices engine and [frinxit].

## Requirements
* [Docker](https://www.docker.com/)
* [Docker Compose](https://github.com/docker/compose)
* JDK 1.8
* License for FRINX ODL

## Getting started
#### Copy license
 Edit the _frinx.license.cfg_ file in FRINX-machine/odl/ folder and copy your license key there.  
 
 *_frinx.license.cfg:_*  
 `token=<your license key>`
 
#### Installation
Go to the FRINX-machine folder and execute the `install.sh` script.
* Builds conductor .jar files.
* Creates docker images.
* Creates external volumes for data persistence.


Should be executed with sudo otherwise it will prompt for your password in the middle of the script.
```bash
cd FRINX-machine
sudo ./install.sh
```


### Startup
In the FRINX-machine folder execute the `startup.sh` script.
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



[FRINX ODL]: <https://frinx.io/odl_distribution>
[Conductor]: <https://github.com/FRINXio/conductor>
[frinxit]: <https://github.com/FRINXio/frinxit>
