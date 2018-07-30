#!/bin/bash

echo 'Health check:'

declare -i result=0

### Check ODl
./wait_for_it.sh localhost:8181
result+=$?

### Check Elastisearch 
#curl -X GET 'http://localhost:9200/_cluster/health'
./wait_for_it.sh localhost:9200
result+=$?

### Check Microservices
./wait_for_it.sh localhost:6000
result+=$?

### Check Coductor-server
./wait_for_it.sh localhost:8080
result+=$?

### Check conductor-ui
./wait_for_it.sh localhost:5000
result+=$?


### Check dynomite
#curl -X GET 'http://host:22222/ping'
exit $result


