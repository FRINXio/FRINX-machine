#!/bin/bash

echo 'Health check:'

### Check ODl
./wait_for_it.sh localhost:8181
### Check Elastisearch 
#curl -X GET 'http://localhost:9200/_cluster/health'
./wait_for_it.sh localhost:9200
### Check Microservicies
./wait_for_it.sh localhost:6000
### Check Coductor-server
./wait_for_it.sh localhost:8080
### Check conductor-ui
./wait_for_it.sh localhost:5000
### Check dynomite
#curl -X GET 'http://host:22222/ping'
