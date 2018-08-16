#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}


### Update submodules
git submodule init
git submodule update --recursive --remote


cd conductor

### Create gradle properties file
echo 'git.root=../' > gradle.properties

### Build conductor
./gradlew build -x test


### Build docker images
cd ${DIR}
echo 'Create external volume for redis'
sudo docker volume create --name=redis_data
sudo docker volume create --name=elastic_data
echo 'Build images'
sudo docker-compose build









