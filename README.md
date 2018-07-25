### Conductor - prototype
The project is a dockerized package of ODL, Netflix - Conductor and a microservices server.

### Requirements
* docker
* docker-compose
* JDK 1.8+
* License for FRINX ODL copied to /home/jozef/conductor-prototype/odl/frinx.license.cfg. ,like token=...

### Getting started
* Execute install.sh script. Builds docker images.
* To start execeute startup.sh. Starts containers and loads frinx workflows and tasks.
* To stop containers 'docker-compose down'.

### Exposed ports
* Conductor-server: 
	* host:8080
	* host:8000

* Conductor-ui: 
	* host:5000

* ODL: 
	* host:8181

* Microservices: 
	* host:6000

* Elasticsearch: 
	* host:9200
	* host:9300
