# FRINX Machine latest release
Please deploy the latest release of FRINX Machine. Follow the link below and copy the zip or tar file to your host where you will run FRINX Machine. Unzip or untar and follow the installation instructions below.

https://github.com/FRINXio/FRINX-machine/releases

> Master branch is used for development and not recommended for deployment


## Requirements
Minimal hardware requirements (See [resource limitation](#resource-limitation))

Production: (default)

- 24GB RAM
- 4x CPU

Development:

- 16GB RAM
- 4x CPU

To deploy an FM swarm cluster you need at least one machine with Ubuntu 18.04/20.04 installed.

# Starting Frinx Machine
You can deploy the FM either locally with all services running on a single node, or you can split UniFlow and UniConfig instances among multiple nodes. UniFlow is always running on the docker swarm manager node. In the case of multi-node deployment, it is necessary to modify the .env file ( Follow [Preparing Environment](#preparing-environment) ).


* [Installation](#installation)
* [Single-node deployment](#single-node-deployment)
* [Multi-node deployment](#multi-node-deployment)
* [Preparing Environment](#preparing-environment)
* [Resource limitation](#resource-limitation) 
* [Maintaining](#maintaining)
* [TLS Certificated](#tls-certificates) 

## Installation
Run the install script, this will check and download the neccessary prerequisities.

```sh
$ sudo ./install.sh
```

Automatically installed software:
- curl
- docker-compose 1.22.0
- docker-ce 18.09 / 20.10
- loki-docker-driver

NOTE: It may happen that swarm initialization will fail during install. Most likely due to multiple network interfaces present. 
In that case run `docker swarm init --advertise-addr <ip-addr>` command to tell swarm which ip address to use for inter-manager communication and overlay networking

NOTE: As FM is designed to run as non-root user, you need the user to be in `docker` group, this is done automatically during the installation process. Use newgrp or reboot the system for changes to take effect **BEFORE** running ```./startup.sh``` <br>
See: https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user

If you want to configure docker to use a proxy server, use:

```sh
# Create folder for docker proxy config file
$ mkdir "${USER}/.docker"

$ sudo ./install.sh \
--proxy-conf "${USER}/.docker/config.json" \ 
--http-proxy "ip:port" \
--https-proxy "ip:port" \
--no-proxy "ip:port,ip:port,..."
```
For disabling proxy, the config.json must be removed and content of UC_PROXY_* variables in .env file must be erased! For example: UC_PROXY_HTTP_ENV="".

For more info see: https://docs.docker.com/network/proxy/

### Install/Update docker secrets (KrakenD HTTPS/TLS)
During installation, docker secrets are created and are used for establishing HTTPS/TLS connections. These secrets contain private and public keys and are generated from files in the ./config/certificates folder. These certificates can be replaced by custom certificates (use the same name) before execution of installation script or re-execution with the `--update-secrets` flag.
## Single-node deployment
Installation and running of UniFlow and UniConfig on the same machine.
To deploy both UniFlow and UniConfig locally (for testing and demo purposes), run `startup.sh`:
```sh
$ ./startup.sh

# To use development resource limitation, use:
$ ./startup.sh --dev 

# To uniflow only, use:
$ ./startup.sh --uniflow 

# To uniconfig only, use:
$ ./startup.sh --uniconfig 

# To metric services only, use:
$ ./startup.sh --monitoring 

```
The FRINX Machine services will now be started. 

To check the status of all services use
```sh
$ docker service ls
```

Each service will show as 'REPLICAS 1/1' when the service is up (it may take several minutes to start all services).

UniFlow dashboard is accessible via web browser by visiting:
```sh
http://<IP_of_node_running_FM>
```
In some cases the self signed certificate of the FM dashboard creates an NET_ERR_CERT_INVALID error message in your browser. Follow [these](https://stackoverflow.com/questions/35274659/does-using-badidea-or-thisisunsafe-to-bypass-a-chrome-certificate-hsts-error) steps to proceed.

### Demo workflows & sample topology
Once all services are started, please clone https://github.com/FRINXio/fm-workflows and follow the instructions to load demo workflows and a sample topolgy. <br>You can find a collection of demo use cases here https://docs.frinx.io/frinx-machine/use-cases/index.html



## Multi-node deployment
UniFlow services are deployed on swarm manager node and UniConifig services are deployed on swarm worker nodes.

NOTE: Before starting multi-node deployment, it is **necessary to generate uniconfig compose files** with `generate_uc_compose.sh` script!
### Preparing worker nodes for UniConfig services

Install and set-up docker-ce on worker node:
```sh
$ sudo apt-get install curl
$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
$ sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
$ sudo apt-get update
# For Ubuntu 18-*
$ sudo apt-get install docker-ce=5:18.09.9~3-0~ubuntu-bionic
# For Ubuntu 20-*
$ sudo apt-get install docker-ce=5:20.10.5~3-0~ubuntu-focal
$ sudo usermod -aG docker $USER
$ newgrp docker
$ docker plugin install grafana/loki-docker-driver:latest --alias loki --grant-all-permissions
```

Run following command on manager node to determine the swarm token
```sh
# on manager node
$ docker swarm join-token worker
```

And then join the worker node to the swarm with token provided by the manager:
```sh
# on worker node
$ docker swarm join --token SWMTKN-<TOKEN> IP:PORT
```

To deploy UniConfig to a worker node, distribute the default UniConfig configuration to `/opt` directory on the worker node (SCP used as an example).

From the manager node:
```sh
$ scp -r ./config/uniconfig/frinx username@host:/home/username/
```
Log into remote node and copy the files:
```sh
$ sudo cp -r /home/username/frinx /opt
$ sudo chmod a+w /opt/frinx/uniconfig/cache/
```

### Generating uniconfig compose files

Now is possible to check all swarm nodes with and find worker node IDs.
```sh
#List all swarm nodes
$ docker node ls
```

For generating of uniconfig (uniconfig-postgresql) compose files use `generate_uc_compose.sh`.  
You need to define:
- uniconfig service name: must be unique name 
- swarm node-id: where will be deployed (find from previous command output)
- folder path:  where are stored composefiles for multinode deployment

Preffered folder path is `./composefiles/uniconfig`, but can be differend (outside from FM repo folder).
```sh
$ ./generate_uc_compose.sh -s <service_name> -n <node_id> -f <path_to_folder>
```

### Deploying services

```sh
# If composefiles path is ./composefiles/uniconfig 
$ ./startup.sh --multinode 
# For different composefiles path
$ ./startup.sh --multinode 'path/to/your/folder'
# Can be aslo combined with another options 
$ ./startup.sh --multinode --uniconfig --dev
```

NOTE: The deployment might take a while as the worker node needs to download all necessary images first.

## Preparing Environment
The FRINX-Machine repository contains a **env.template** (used for creating .env) and **.env** file in which the default FM configuration settings are stored. In .env file, the settings are divided to these groups:

* **Common setting** 
>   * BASE_KRAKEND_IMAGE_TAG :  Define frinx krakend image tag
>       * Used for building image with uniconfig certificates (./build_krakend.sh)
>       * Used for FM krakend service, if special certificates are not required

>   * LOCAL_KRAKEND_IMAGE_TAG : KrakenD local image tag settings
>       * Tag for image with uniconfig certificates
>       * Generated by ./build_krakend.sh script 
>       * Default tag is 'with_certificates'
>       * If empty, then is used BASE_KRAKEND_IMAGE_TAG value

* **Temporary settings** - Created by FM scripts, **do not change them**
>   * UC_PROXY_* : use docker proxy in Uniconfig Service ( See [Installation](#installation) )

Default settings are prepared for deployment without docker proxy.
## Resource limitation

Default resource limitation is configured for production but can be changed to development.
```sh
$ ./startup.sh --dev
```
Template for production settings is stored in `./config/prod_settings.txt`. <br> In this file, these values can be changed by profiled requirements.

## Maintaining

### Checking
You can check the status of the swarm cluster by running:
```sh
$ docker service ls
$ docker stack ps fm
```
Where 'fm' (FRINX Machine) is the name of the swarm stack configured during deployment, the name is assigned automatically.

### Bench Security

For security improvement of dockerized Frinx Machine, therse docker settings can be configured to `/etc/docker/daemon.json`. 

```sh
$ cat /etc/docker/daemon.json

{
    "icc": false,
    "log-driver": "syslog",
    "userland-proxy": false,
    "no-new-privileges": true
}
```
Config file is stored in `./config/docker-security/` folder. <br>
Bench security analysis can be performed with this command
```sh
$ ./config/docker-security/bench_security.sh
```

### Monitoring services

Frinx Machine is collecting logs and metrics/statistics from services.
* Metrics: Prometheus
* Logs: Loki
* Node monitoring: node-exporter
* Swarm monitoring: google/cadvisor
* Visualization: Grafana (url 127.0.0.1:3000)
<br>

### ElasticSearch disk flood stage prevention 
ElasticSearch changes the disk permissions to read-only if the disk free space drops below 512Mb.. This setting is a last resort to prevent nodes from running out of disk space. The index block must be released manually when the disk utilization falls below the high watermark.
```sh
# from fm_elasticsearch container
curl -XPUT -H "Content-Type: application/json" http://localhost:9200/_all/_settings -d '{"index.blocks read_only_allow_delete": null}'
```

### List of deployed uniconfig services
KrakenD provice API, which return list of deployed uniconfig services:

```sh
$ curl -X GET 127.0.0.1/static/list/uniconfig
{"instances":["uniconfig1","uniconfig2"]}
```

### Shutdown
To stop all services, simply remove the stack from the swarm:
```sh
$ ./teardown.sh
```

To remove all persistent data, purge the volumes (ATTENTION!!! ALL USER DATA WILL BE LOST):
```sh
$ ./teardown.sh -v # remove Frinx Machine uniflow/uniconfig data
$ ./teardown.sh -m # remove Monitoring data
$ ./teardown.sh -a # remove all Frinx docker volumes
```
For see more options run:
```sh
$ ./teardown.sh -h
```


### Log collections
To collect logs, run:
```sh
$ ./collectlogs.sh
```
This will collect all docker related logs and compresses it into an archive. Logs are collected from local machine only, if you want logs from remote node (e.g. worker) you must copy and run the script on the remote node.

# TLS certificates

In the demo deployment the setup has already been done and uniconfig is running under https(not suitable for production).
To set it up with own certificates please follow the next steps:

1.
    ```
    rm /home/test/FRINX-machine/config/uniconfig/frinx/uniconfig/config/.keystore
    rm krakend/certs/*
    ```
2.
    See `TLS-based authentication` on https://docs.frinx.io/frinx-odl-distribution/oxygen/user-guide/restconf.html
    Now you can set up the new keystore in `/home/test/FRINX-machine/config/uniconfig/frinx/uniconfig/config/`. 

    In case a new certificate is generated for uniconfig When prompted for `What is your first and last name?` put docker dns name of uniconfig container (Default: uniconfig).

    Also will need to modify `/home/test/FRINX-machine/config/uniconfig/frinx/uniconfig/config/lighty-uniconfig-config.json` based on the new keystore setup.  
3.  In case self signed certificate is used please add ca's certificate to `karakend/certs` folder in `.crt` format.  
    For changes to be propagated run `./build_krakend.sh` (for more run with -h) in case of deployed stack `startup.sh` as well. 

## For developers
If you need to modify and rebuild modules, you can use `pullmodules.sh` script to download up-to-date modules from FRINX's public GitHub repositories. Then you can use standard docker utilities to build and distribute them, e.g.:
```sh
$ cd build/uniconfig
$ docker build .
```

### ElasticSearch disk flood stage prevention 
ElasticSearch changes the disk permissions to read-only if the disk free space drops below 512Mb.. This setting is a last resort to prevent nodes from running out of disk space. The index block must be released manually when the disk utilization falls below the high watermark.
```sh
# from fm_elasticsearch container
curl -XPUT -H "Content-Type: application/json" http://localhost:9200/_all/_settings -d '{"index.blocks.read_only_allow_delete": null}'
```
### Building and distribution of custom images
In case you need to test a custom image you've built on a remote node, follow these steps:

Build an image with an unique name
```sh
$ docker build . -t domain/imagename:version
```
Export the image to .tar archive
```sh
$ docker save --output image.tar domain/imagename:version
```
(Optional) Compress the image - images can get quite big
```sh
$ tar -cjf image.tar.bz2 image.tar
```
Copy the file to remote node (for example via SCP)
```sh
$ scp image.tar.bz2 username@remotehost:/path/to/folder
```
On the remote node:

(Optional) Decompress the image
```sh
$ tar -xvf image.tar.bz2
```
Load the image into local repository
```sh
$ docker load --input image.tar
```
Update the service
```sh
$ docker service update --image domain/imagename:version
```

NOTE: If the service has any healthchecks, make sure they also work in the new version of the image, otherwise the service will appear as unhealthy and refuse to start. In such case you will need to remove or modify the healthcheck.

## License
A 30-day trial license of UniConfig is included, if you would like to change the license, replace the license string in file `config/uniconfig/uniconfig_license.txt` with your own.
