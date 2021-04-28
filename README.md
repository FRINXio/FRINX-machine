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


* [Preparing Environment](#preparing-environment)
* [Installation](#installation)
* [Single-node deployment](#single-node-deployment)
* [Multi-node deployment](#multi-node-deployment)
* [Resource limitation](#resource-limitation) 
* [Maintaining](#maintaining)
* [TLS Certificated](#tls-certificates) 

## Preparing Environment
The FRINX-Machine repository contains a **env.template** (used for creating .env) and **.env** file in which the default FM configuration settings are stored. In .env file, the settings are divided to three groups:

* **Common setting** 
>   * LOCAL_KRAKEND_IMAGE_TAG : KrakenD local image tag settings
>       * Can be changed by user before starting ./install.sh 
* **Multi-node settings** 
>   * UC_SWARM_NODE_ID : ID of swarm worker node, where uniconfig will be deployed
>       * Must be defined by user before multi-node deployment

* **Temporary settings** - Created by FM scripts, **do not change them**
>   * UC_PROXY_* : use docker proxy in Uniconfig Service ( See [Installation](#installation) )

Default settings are prepared for single-node deployment.

For multi-node deployment, you must set ID of worker node to UC_SWARM_NODE_ID variable.

```sh
# How to list swarm nodes
$ docker node ls
# Print ID of worker
$ docker node ls --filter role=worker --format {{.ID}}
```
## Installation
Run the install script, this will check and download the neccessary prerequisities.

```sh
$ sudo ./install.sh
```

Automatically installed software:
- curl
- docker-compose 1.22.0
- docker-ce 18.09
 

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

# FM without micros, use:
$ ./startup.sh --no-micros 
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
UniFlow services are deployed on swarm manager node and UniConifig services are deployed on swarm worker node.

NOTE: Before starting multi-node deployment, it is **necessary to set the ENVIRONMENT variables** in the .env file! [Preparing Environment](#preparing-environment)

### Preparing worker node for UniConfig services

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
```

### Deploying services

Now is possible to check swarm nodes with and find worker node ID
```sh
$ docker node ls
$ docker node ls --filter role=worker --format {{.ID}} 
```
Worker node ID `must be stored` into UNICONFIG_ID variable in .env file. <br>
Then Frinx Machine services can be started with command.

```sh
$ ./startup.sh --multinode
```

NOTE: The deployment might take a while as the worker node needs to download all necessary images first.

It is possible to deploy UniFlow services without service "micros" (default UniConfig workers and workflows):
```sh
$ ./startup.sh --multinode --no-micros
```

NOTE: Flag `--no-micros` can be also used in single-node deployment.

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

### Shutdown
To stop all services, simply remove the stack from the swarm:
```sh
$ ./teardown.sh
```

To remove all persistent data, purge the volumes (ATTENTION!!! ALL USER DATA WILL BE LOST):
```sh
$ ./teardown.sh -v
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
    For changes to be propagated run `install.sh` in case of deployed stack `startup.sh` as well. 

## For developers
If you need to modify and rebuild modules, you can use `pullmodules.sh` script to download up-to-date modules from FRINX's public GitHub repositories. Then you can use standard docker utilities to build and distribute them, e.g.:
```sh
$ cd build/uniconfig
$ docker build .
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
