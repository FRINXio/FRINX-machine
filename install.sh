#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}


### Add microservicies repository
cd microservicies
git submodule add -b simple https://github.com/FRINXio/netinfra_utils.git
git submodule init 
git submodule update --remote netinfra_utils

cd ${DIR}

### Add conductor repository
git submodule add https://github.com/Netflix/conductor.git
git submodule init
cd conductor
git checkout 'v1.10.10'


### Set load kitchenthin on default false
sed -i "s/loadSample=true/loadSample=false/g"  ./docker/server/config/config-local.properties
sed -i "s/loadSample=true/loadSample=false/g"  ./docker/server/config/config.properties


### Build conductor server
cd server
../gradlew build

### Build docker containers
cd ${DIR}
sudo docker-compose build









