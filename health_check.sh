#!/bin/bash

echo 'Health check:'

declare -i result=0

### Check ODl
echo Check ODL availability:

result=1
for i in {30..1}; do
  response=$(curl --user admin:admin --silent --write-out "HTTPSTATUS:%{http_code}" -H "Accept: application/json" -X GET "http://127.0.0.1:8181/restconf/modules")
  HTTP_STATUS=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
  if [ $HTTP_STATUS -eq 200 ]; 
  then
    echo ODL is ready
    result=0
    break;
  else
    echo "Not available. Waiting for 30 seconds and retrying $(($i-1)) more times."
    sleep 30
  fi
done

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
