#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}


### Add microservices repository
cd microservices
git submodule add -b simple https://github.com/FRINXio/netinfra_utils.git
git submodule init 
git submodule update --remote netinfra_utils

cd ${DIR}

### Add conductor repository
git submodule add https://github.com/Netflix/conductor.git
git submodule init
cd conductor
git checkout 'v1.10.10'

### Create gradle properties file
echo 'git.root=../' > gradle.properties

### Set load kitchenthin on default false
sed -i "s/loadSample=true/loadSample=false/g"  ./docker/server/config/config-local.properties
sed -i "s/loadSample=true/loadSample=false/g"  ./docker/server/config/config.properties


### Build conductor
./gradlew build

### Build docker containers
cd ${DIR}
sudo docker-compose build









