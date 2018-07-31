#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

### Add conductor repository
git submodule add https://github.com/FRINXio/conductor.git

### Add microservices repository
cd microservices
git submodule add -b simple https://github.com/FRINXio/netinfra_utils.git


cd ${DIR}

### Update submodules
git submodule update --remote

cd conductor


### Create gradle properties file
echo 'git.root=../' > gradle.properties

### Set load kitchenthin on default false
sed -i "s/loadSample=true/loadSample=false/g"  ./docker/server/config/config-local.properties
sed -i "s/loadSample=true/loadSample=false/g"  ./docker/server/config/config.properties


### Build conductor
./gradlew build

### Build docker images
cd ${DIR}
echo 'Create external volume for redis'
sudo docker volume create --name=data
echo 'Build images'
sudo docker-compose build









