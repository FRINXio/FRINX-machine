# FRINX Machine latest release 

## Deprecation warning

> [!CAUTION]
> **Docker swarm deployment is deprecated**. <br> 
> Please follow the Kubernetes installation https://artifacthub.io/packages/helm/frinx-helm-charts/frinx-machine

## General

Please deploy the latest release of FRINX Machine. Follow the link below and copy the zip or tar file to your host where you will run FRINX Machine. Unzip or untar and follow the installation instructions below.

https://github.com/FRINXio/FRINX-machine/releases

> Master branch is used for development and not recommended for deployment

</br>

## Uniconfig license
**Uniconfig docker image has been moved to a private repository** <br>
**For access, contact info@frinx.io**

## Requirements
Minimal hardware requirements (See [resource limitation](#resource-limitation))

Production: (default)

- 24GB RAM
- 8x CPU

Development:

- 16GB RAM
- 4x CPU

It is recommended to deploy with 40GB of disk space or more depending on your data retention policies and deployment scale.

To deploy an FM swarm cluster you need at least one machine with Ubuntu 18.04/20.04 installed.

## Frinx Machine architecture
Architecture overview [here](docs/fm_architecture.md).

# How to install and run FRINX Machine
You can deploy the FM either locally with all services running on a single node, or you can distribute Workflow-Manager and UniConfig instances across multiple nodes. Workflow-Manager is always running on the docker swarm manager node.


* [Installation](#installation)
* [Single-node deployment](#single-node-deployment)
* [Multi-node deployment](#multi-node-deployment)
* [Resource limitation](#resource-limitation) 
* [Maintaining](#maintaining)
* [TLS in Frinx Machine](#tls-in-frinx-machine) 
</br></br>
## Installation
Run the install script, this will check and download the necessary prerequisites.

```sh
$ ./install.sh                   # pull images, set secrets, skip the installation of dependencies
$ ./install.sh  --install-deps   # required sudo access to install the FM dependencies (see list below) 
$ ./install.sh  --update-secrets # create/update certificates to docker secrets frm ./config/certificates folder

# Use custom cert/key for KrakenD TLS, replace old frinx_krakend_tls* docker secrets
$ ./install.sh  --custom-ssl-cert path/to/cert.pem --custom-ssl-key path/to/key.pem 
```

Automatically installed software:
- curl
- docker-ce 18.09 / 20.10
- loki-docker-driver
- openssl

NOTE: For migration from older version of docker to newer see https://docs.docker.com/engine/install/ubuntu/. <br>
To configure permission, follow https://docs.docker.com/engine/install/linux-postinstall/.

NOTE: It may happen that swarm initialization will fail during install. Most likely due to multiple network interfaces present. 
In that case run `docker swarm init --advertise-addr <ip-addr>` command to tell swarm which ip address to use for inter-manager communication and overlay networking

</br>

NOTE: As FM is designed to run as non-root user, you need the user to be in `docker` group, this is done automatically during the installation process. Use newgrp or reboot the system for changes to take effect **BEFORE** running ```./startup.sh``` <br>
See: https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user

</br>

### Enable Azure AD authorization

Frinx Machine supports authentication and authorization via Azure AD.
For details about configuration visit [Azure AD configuration](docs/azure_ad.md).

For configuration use `azure_ad.sh` script.

You need to define:
- tenant name: organization name (single tenant e.g. `yourAdName.onmicrosoft.com`), or `common` for multi tenant
- tenant id: code of tenant AD (GUID), e.g. aaaaaaaa_bbbb_cccc_dddd_eeeeeeeeeeee

- client id: code of application (GUID) for KrakenD plugin (see [KrakenD Azure Plugin docs](https://github.com/FRINXio/krakend-azure-plugin))
- client secret: application secret 
- redirect url: IP/DNS of server, from where is accessed frinx-frontend

```sh
# print help for configuration
$ ./azure_ad.sh configure -h
# example for multi-tenant
$ ./azure_ad.sh configure --azure_enable \
    --tenant_name 'common' \
    --tenant_id 'aaaaaaaa_bbbb_cccc_dddd_eeeeeeeeeeee' \
    --client_id 'aaaaaaaa_bbbb_cccc_dddd_eeeeeeeeeeee' \
    --client_secret '79A4Q~RL5pELYji-KU58UfSeGoRVGco8f20~K' \
    --redirect_url 'localhost'
```
These settings will be stored in docker secrets with name frinx_auth. 
Default configuration can be found in file **config/secrets/frinx_auth**.
Other options are follow:

```sh
# Save configuration to file config/secrets/frinx_auth.tmp
$ ./azure_ad.sh configure --azure_enable \
    --tenant_name 'common' \
    --tenant_id 'aaaaaaaa_bbbb_cccc_dddd_eeeeeeeeeeee' \
    --client_id 'aaaaaaaa_bbbb_cccc_dddd_eeeeeeeeeeee' \
    --client_secret '79A4Q~RL5pELYji-KU58UfSeGoRVGco8f20~K' \
    --redirect_url 'localhost'
    --keep_config

# Validate values in config/secrets/frinx_auth.tmp 
$ ./azure_ad.sh validate 

# Update/create frinx_auth docker setrets from config/secrets/frinx_auth.tmp 
$ ./azure_ad.sh updateSecrets 
```
<br>


### Install/Update docker secrets (KrakenD HTTPS/TLS)
During installation, docker secrets are created and are used for establishing HTTPS/TLS connections. These secrets contain private and public keys and are generated from files in the ./config/certificates folder. 

These certificates can be replaced by custom certificates (use the same name) before execution of installation script or re-execution with the `--update-secrets` flag. </br></br>
## Single-node deployment
Install and run Workflow-Manager and UniConfig on the same machine.
To deploy all components except unistore on a single node, run `startup.sh`:
```sh
$ ./startup.sh

# To deploy FRINX Machine with resource limitations (e.g. for development), use:
$ ./startup.sh --dev 

# To deploy all services including unistore, use:
$ ./startup.sh --with-unistore

# To deploy workflow-manager only, use:
$ ./startup.sh --workflow-manager 

# To deploy uniconfig only, use:
$ ./startup.sh --uniconfig 

# To deploy unistore services only, use:
$ ./startup.sh --unistore

# To deploy monitoring services only, use:
$ ./startup.sh --monitoring 

# To deploy FRINX Machine without monitoring services, use:
$ ./startup.sh --no-monitoring 

# To deploy FRINX Machine with kafka and debezium:
$ ./startup.sh --with-kafka 

```
The FRINX Machine services will be started.

To check the status of all services use
```sh
$ docker service ls
```

Each service will show as 'REPLICAS 1/1' when the service is up (it may take several minutes to start all services).

The FRINX Machine dashboard is accessible via web browser by visiting:
```sh
http://<IP_of_node_running_FM>

# monitoring dashboard
http://<IP_of_node_running_FM>:3000
```

In some cases the self signed certificate of the FM dashboard creates an NET_ERR_CERT_INVALID error message in your browser. Follow [these](https://stackoverflow.com/questions/35274659/does-using-badidea-or-thisisunsafe-to-bypass-a-chrome-certificate-hsts-error) steps to proceed.

</br>

### Demo workflows & sample topology
Once all services are started, please clone https://github.com/FRINXio/fm-workflows and follow the instructions to load demo workflows and a sample topolgy. <br>You can find a collection of demo use cases here https://docs.frinx.io/frinx-machine/use-cases/index.html

</br>

## Multi-node deployment
Workflow-Manager services are deployed on swarm manager node and UniConifig services are deployed on swarm worker nodes.

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
$ docker plugin install grafana/loki-docker-driver:main-20515a2 --alias loki --grant-all-permissions
```

### Connect workers to Docker Swarm

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

Now is possible to check all swarm nodes with and find worker node IDs.
```sh
#List all swarm nodes
$ docker node ls
```

### Generate configuration files for multi-node deployment

Frinx Machine supports Uniconfig deployment in multi-zone mode (multiple uniconfig zones).
Before the Frinx Machine is start, is necessary to generate unique configuration files per each zone separately.
For generating these files use `generate_uc_compose.sh`.  

You need to define:
- uniconfig zone name: must be unique name - <service_name>
- folder path:  where are stored composefiles for multinode deployment
- instances: how many uniconfig instances will be started per zone (redundancy)

- swarm node placement method: swarm node identificator, select one of them (use `docker node ls` for info)
    *   node id : unique ID od node
    *   node hostname : unique node hostname
    *   node role : manager/worker1/worker2 ...
    *   node label : node with label zone=<NODE_LABEL> 

Script is checking input placement values based on Readiness status. Files are not generated by default, when
nodes are not ready. This generation of composefiles can be forced with flag --force. 
Default folder path is `./composefiles/uniconfig`, but can be different (outside from FM repo folder).

```sh
# Check all nodes in cluster (from manager node)
$ docker node ls

m4lyotjrwc059u76dkdksyfsp *   frinx-manager   Ready     Active         Leader           20.10.5
vrybz35tsmtp23gd9byoimq1z     frinx-worker1   Ready     Active                          20.10.5
li5msj11609ss58n7mafa9cbt     frinx-worker2   Ready     Active                          20.10.5

# Check settings of nodes in cluster
docker node inspect <HOSTNAME> --format "{{.Description.Hostname}} {{.ID}} {{.Spec.Labels.zone}} {{.Spec.Role}}"
docker node inspect --format '{{.Description.Hostname}} {{.ID}} {{.Spec.Labels.zone}} {{.Spec.Labels.db}} {{.Spec.Role}}' $(docker node ls -q)
  <Hostname>             <ID>             <Zone Label>  <Zone DB Label>   <Role>
frinx-manager   m4lyotjrwc059u76dkdksyfsp   workflow-manager        <no value>     worker
frinx-worker1   vrybz35tsmtp23gd9byoimq1z  uniconfig        uniconfig     worker
frinx-worker2   9l6k8qg6rl6wn3tv8o7s29464  uniconfig       <no value>     worker

# Check
$ ./generate_uc_compose.sh -s <service_name> -f <path_to_folder> -i <instances> --hostname <Hostname>
$ ./generate_uc_compose.sh -s <service_name> -f <path_to_folder> -i <instances> --node-id <ID>
$ ./generate_uc_compose.sh -s <service_name> -f <path_to_folder> -i <instances> --label <Label>
$ ./generate_uc_compose.sh -s <service_name> -f <path_to_folder> -i <instances> --role <Role>

# Label swarm node with zone label
docker node update <NODE_HOSTNAME> --label-add zone=<UNIQUE_ZONE_LABEL>

# One 
docker node update <NODE_HOSTNAME> --label-add db=<UNIQUE_ZONE_LABEL>

# Force generating of composefiles, e.g.
$ ./generate_uc_compose.sh -s <service_name> -f <path_to_folder> -i <instances> --role <Role> --force
```

For enhanced FM architecture deployment is recommended to use label base placement, where nodes are split into zone groups by node label zone=<UNIQUE_ZONE_LABEL>. In each group must be only one node with label db=<UNIQUE_ZONE_LABEL>. 

To see diagram visit [Frinx Machine Architecture](docs/fm_architecture.md).

<br>

### Preparing worker/slave node for multi-node deployment

To deploy UniConfig to a worker node, create cache folder and clean old uniconfig volumes.

From the worker node:
```sh
# create cache volume for uniconfig-cotroller
mkdir -p /opt/frinx/<SERVICE_NAME>/uniconfig-controller/cache/
# set correct permissions
chmod -R 777 /opt/frinx/<SERVICE_NAME>/uniconfig-controller/cache/

# if older FM was started on this node, remove docker persistent volumes
docker volume prune --filter label=fm
```
</br>

### Deploying services

```sh
# If composefiles path is ./composefiles/uniconfig 
$ ./startup.sh --multinode 
# For different composefiles path
$ ./startup.sh --multinode 'path/to/your/folder'
# Can be also combined with another options 
$ ./startup.sh --multinode 'path/to/your/folder' --uniconfig --dev
$ ./startup.sh --multinode 'path/to/your/folder' --workflow-manager --dev
```

NOTE: The deployment might take a while as the worker node needs to download all necessary images first.

</br>

## Proxy configuration

Use default environment settings
```sh
# Use $HTTPS_PROXY $HTTP_PROXY $NO_PROXY env
$ ./startup.sh --proxy
```
For customization of proxy settings in FM deployment, create FRINX-Machine/.proxy file and configure own settings.

```ini
HTTP_PROXY='host:port'
HTTPS_PROXY='host:port'
NO_PROXY='ip:port,ip:port'
```
and start FM with --proxy switch.

## Resource limitations

Default resource limitations are configured for production and can be changed for development.
```sh
$ ./startup.sh --dev    # ./config/dev_settings.txt
$ ./startup.sh --prod   # ./config/prod_settings.txt, same as ./startup.sh 
$ ./startup.sh --high   # ./config/high_settings.txt, Warning, will be used a lot of resources.
```
These values in the dev_settings and prod_settings txt files can be changed based on deployment needs.

</br>

## Maintaining

### Checking
You can check the status of the swarm cluster by running:
```sh
$ docker service ls
$ docker stack ps fm
```
Where 'fm' (FRINX Machine) is the name of the swarm stack configured during deployment, the name is assigned automatically.

</br>

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

</br>

### Monitoring services

Frinx Machine is collecting logs and metrics/statistics from services.
* Metrics: InfluxDB
* Logs: Loki
* Node monitoring: Telegraf
* Swarm monitoring: Telegraf
* Visualization: Grafana (url 127.0.0.1:3000, user: frinx, password: frinx123!)

NOTE: Be aware, that the monitoring system is space consuming. For longer monitoring is good to have enough free space on the disc. 
Optimal is 30Gb and more.

Default grafana credentials can be changed in `config/secrets/frinx_grafana`

</br>

### List of deployed uniconfig services
KrakenD provide API, which return list of deployed uniconfig services:

```sh
$ curl -X GET 127.0.0.1/static/list/uniconfig
{"instances":["uniconfig1","uniconfig2"]}
```

</br>

### Shutdown
To stop all services, simply remove the stack from the swarm:
```sh
$ ./teardown.sh
```

To remove all persistent data, purge the volumes (ATTENTION!!! ALL USER DATA WILL BE LOST):
```sh
$ ./teardown.sh -f # remove Frinx Machine workflow-manager/uniconfig data
$ ./teardown.sh -m # remove Monitoring data
$ ./teardown.sh -v # remove all Frinx docker volumes
$ ./teardown.sh -c # delete content of ./config/uniconfig/frinx/uniconfig/cache folder
$ ./teardown.sh -a # delete all volumes and files
```
For see more options run:
```sh
$ ./teardown.sh -h
```

</br>

### Log collections
To collect logs, run:
```sh
$ ./collectlogs.sh
```
This will collect all docker related logs and compresses it into an archive. Logs are collected from local machine only, if you want logs from remote node (e.g. worker) you must copy and run the script on the remote node.

</br>

## TLS in Frinx Machine

Frinx Machine is providing the option to establish TLS connections between:
* Between browser and api-gateway (by default off, to enable use follow command `./startup.sh --https`). [More info](https://www.krakend.io/docs/service-settings/tls/)
* Frinx Machine Services and Uniconfig zone (Traefik load-balancer). [More info](https://doc.traefik.io/traefik/https/tls/)


During the execution of `./install.sh`, all certificates are stored to docker secrets. 
For Traefik/Uniconfig zone, the script generates its own keys/certs and store them in the `./config/certificates` folder.
For KrakenD can be these certificates specified: `$ ./install.sh  --custom-ssl-cert path/to/cert.pem --custom-ssl-key path/to/key.pem`

### Certificate description
Api-Gateway (KrakenD) TLS: 
* frinx_krakend_tls_cert.pem 
* frinx_krakend_tls_key.pem

Traefik certificates/keys: Establish HTTPS connection between FM services and Uniconfig zone (multizone support)

* frinx_uniconfig_tls_cert.pem 
* frinx_uniconfig_tls_key.pem

Uniconfig-postgres certificates/keys: Establish TLS connection for all uniconfig-postgres instances (multi-zone support)

* frinx_uniconfig_tls_cert.pem 
* frinx_uniconfig_tls_key.pem

Uniconfig-controller keys: Used for establishing secured communication with uniconfig-postgres (multi-zone support)

* frinx_uniconfig_tls_key.pem
* frinx_uniconfig_tls_key.der
* frinx_uniconfig_tls_key.p12

</br>

! For use in the **production environment**, please use your own certificates for KrakenD service.

```bash
# Example, generate private key
$ openssl genrsa --out FRINX-Machine/config/certificates/frinx_krakend_tls_key.pem 
# Example, generate selfsigned x509 cert
# used wildcard Common Name (CN) *
$ openssl req -new -x509 -days 365 -addext 'subjectAltName = DNS:*'
            -key FRINX-Machine/config/certificates/frinx_krakend_tls_key.pem \
            -out FRINX-Machine/config/certificates/frinx_krakend_tls_cert.pem \
            -subj '/C=SK/ST=Slovakia/L=Bratislava/O=Frinx/OU=Frinx Machine/CN=*/emailAddress=frinx@frinx.io'
```

</br>

### Configuring max storage usage per service

**Conductor** external storage persistence can be configured via parameters in `config/conductor/config.properties`.

```sh
# default values
conductor.external-payload-storage.postgres.max-data-rows=1000000
conductor.external-payload-storage.postgres.max-data-days=0
conductor.external-payload-storage.postgres.max-data-months=0
conductor.external-payload-storage.postgres.max-data-years=1
```

**InfluxDB** max retention period via variable in `composefiles/support/swarm-monitoring.yml`

```yml
# default value for frinx bucket
      - DOCKER_INFLUXDB_INIT_RETENTION=2d
```

**Loki** max retention period can be configured in `config/monitoring/loki/loki-config.yaml`.


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

